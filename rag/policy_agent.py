"""Policy Agent v2.1 : analyse de couverture d'un dossier à partir du JSON de l'Intake Agent.

Usage :
    python rag/policy_agent.py D01 D02 D07     # test sur des dossiers synthétiques
    python rag/policy_agent.py D02 --sans-cache
    python rag/policy_agent.py D02 --avec-reformulation

    from policy_agent import analyse_couverture
    resultat = analyse_couverture(intake)

Étapes :
1. 3 à 6 sous-questions déterministes à partir du dossier et des conditions particulières
   (garantie souscrite, exclusions, franchise, responsabilité si un tiers est impliqué,
   délai de déclaration, conducteur s'il n'est pas désigné au contrat, déclaration du
   risque si l'usage diffère de l'usage déclaré ou si le conducteur n'est pas désigné).
2. Reformulation par Gemini dans le vocabulaire du contrat et du Code (prompt R1,
   prompts/PROMPTS.md), désactivée par défaut (--avec-reformulation, reformulation=True).
   En cas d'échec, on garde les questions d'origine.
3. retriever.search(k=5) sur chaque question (origine + reformulée) ; fusion par
   article, au plus 10 articles : les 2 meilleurs de chaque recherche d'office, au moins 4
   du contrat quand il y en a parmi les résultats, puis la somme des scores RRF.
4. Réponse de couverture par Gemini (prompt P4 v2), en JSON uniquement. Le prompt reçoit
   le dossier, les conditions particulières et les articles dans trois sections distinctes ;
   au-delà de ~6 000 tokens, chaque article est réduit à son chunk le mieux classé.
5. Contrôle : un article cité qui n'a pas été fourni est retiré et la confiance baisse ;
   JSON invalide, aucun article valide ou erreur d'appel → verdict « indetermine ».

Configuration : LLM_PROVIDER choisit le fournisseur, gemini (défaut) ou ollama ; les deux
sont appelés via l'endpoint /chat/completions compatible OpenAI.
- gemini : GEMINI_API_KEY (obligatoire, jamais dans le code), GEMINI_MODEL (défaut :
  gemini-3.8-flash, modèle stable de la documentation Gemini en octobre 2026), comme le
  workflow n8n, avec reasoning_effort (documenté pour cet endpoint : minimal, low, medium,
  high) pris dans GEMINI_REASONING_EFFORT, « low » par défaut ; une valeur vide ne l'envoie pas.
  Au moins MIN_INTERVAL_S entre deux appels (offre gratuite).
- ollama : OLLAMA_BASE_URL (défaut http://localhost:11434, endpoint /v1), OLLAMA_POLICY_MODEL
  (défaut qwen2.5:3b, comme le .env.example de la branche ines). Ni clé API ni reasoning_effort.
  response_format json_schema est accepté : Ollama passe le schéma à son paramètre format
  (openai/openai.go ; docs.ollama.com/capabilities/structured-outputs). Le JSON reste validé ici.
La trace contient le fournisseur, la taille du prompt P4 et la durée de chaque appel.

Cache disque des réponses du LLM dans cache_llm/ : la clé est un hash du fournisseur, du
modèle, du reasoning_effort et du prompt complet (système + utilisateur). Pour Gemini, le
fournisseur n'entre pas dans la clé, qui reste celle des réponses déjà en cache.
Une réponse en cache ne consomme aucune requête ; dans la trace, l'appel a le statut
« cache ». --sans-cache (ou cache=False) force un nouvel appel, dont la réponse remplace
celle du cache.

Champs ajoutés au schéma P1 (optionnels) :
- conditions_particulieres : {garanties, usage_declare, conducteurs_designes, date_souscription},
  ce qui a été souscrit et déclaré (contrat_reference dans les dossiers de test) ;
- souscripteur : nom du souscripteur, utilisé seulement si conducteurs_designes est absent.
"""
import argparse, hashlib, json, os, re, sys, time, urllib.error, urllib.request
from pathlib import Path
from chunking import n_tokens

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "cache_llm"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
DEFAULT_MODEL = "gemini-3.8-flash"
OLLAMA_DEFAULT_URL = "http://localhost:11434"
OLLAMA_DEFAULT_MODEL = "qwen2.5:3b"
MAX_ATTEMPTS = 3          # 1 appel + 2 nouveaux essais
TIMEOUT_S = 120
OLLAMA_TIMEOUT_S = 600    # modèle local, parfois sur CPU : un prompt P4 de ~6 000 tokens est long
# offre gratuite : 5 requêtes par minute (HTTP 429 « limit: 5 » observé) → au moins 13 s entre deux appels
MIN_INTERVAL_S = float(os.environ.get("GEMINI_MIN_INTERVAL_S", 13))
_dernier_appel = [0.0]


def backoff(attempt):
    return 5 * 2 ** (attempt - 1)  # 5 s, puis 10 s (erreurs 503 « surchargé » souvent en rafale)
RETRYABLE_HTTP = {429, 500, 502, 503, 504}
K_PAR_QUESTION = 5
MAX_ARTICLES = 10
MAX_QUESTIONS = 6
PAR_RECHERCHE = 2         # meilleurs articles gardés d'office pour chaque recherche
MIN_ARTICLES_CONTRAT = 4
MAX_PROMPT_TOKENS = 6000  # estimation cl100k ; au-delà, un seul chunk par article
VERDICTS = {"couvert", "non_couvert", "partiel", "indetermine"}
CONFIANCES = ["haute", "moyenne", "basse"]

TYPES = {"collision": "collision", "sortie_de_route": "sortie de route sans autre véhicule", "vol": "vol",
         "tentative_vol": "tentative de vol", "bris_de_glace": "bris de glace", "incendie": "incendie",
         "climatique": "événement climatique", "autre": "autre sinistre"}

# Garanties du contrat susceptibles de couvrir chaque type de sinistre, de la plus spécifique
# à la plus large (la collision suppose un autre véhicule : article 7 du contrat).
GARANTIES_PAR_TYPE = {"collision": ["dommages_collision", "dommages_tous_accidents"],
                      "sortie_de_route": ["dommages_tous_accidents"],
                      "vol": ["vol"], "tentative_vol": ["vol"],
                      "bris_de_glace": ["bris_de_glace", "dommages_tous_accidents"],
                      "incendie": ["incendie_evenements_climatiques", "dommages_tous_accidents"],
                      "climatique": ["incendie_evenements_climatiques", "dommages_tous_accidents"],
                      "autre": ["dommages_tous_accidents"]}
NOMS_GARANTIES = {"responsabilite_civile": "responsabilité civile", "dommages_tous_accidents": "dommages tous accidents",
                  "dommages_collision": "dommages collision", "bris_de_glace": "bris de glace", "vol": "vol",
                  "incendie_evenements_climatiques": "incendie et événements climatiques",
                  "assistance": "assistance", "garantie_conducteur": "garantie du conducteur"}

# Prompts : texte identique à prompts/PROMPTS.md (R1 v1 et P4 v1), à garder synchronisé.
PROMPT_R1 = """Tu aides un moteur de recherche documentaire en assurance automobile.
On te donne des questions sur un dossier de sinistre, rédigées en langage courant.
Réécris chaque question avec le vocabulaire juridique employé dans un contrat d'assurance auto
et dans le Code des assurances, pour qu'elle retrouve les bons articles.

Règles :
- Réponds UNIQUEMENT avec un objet JSON valide : {"reformulations": [{"id": int, "reformulee": "string"}]}.
- Une reformulation par question, avec le même id. Une seule phrase, au plus 30 mots.
- Garde le sens et les faits de la question. N'ajoute aucun fait, aucun montant, aucune conclusion.
- Remplace les mots courants par les termes techniques, et ajoute les notions juridiques proches. Exemples :
  "victime" → "tiers lésé, action directe" ; "documents" → "pièces à fournir" ;
  "délai pour agir en justice" → "prescription" ; pays étranger → "territorialité, carte verte" ;
  "facture gonflée" → "majoration du montant, fausse déclaration" ; "emprunter la voiture" → "prêt du volant, conducteur non désigné" ;
  "activité rémunérée" → "usage du véhicule, transport de personnes à titre onéreux".
- Ne cite pas de numéro d'article."""

PROMPT_P4 = """Tu es un analyste couverture dans un service de gestion des sinistres automobiles.
On te donne trois sections :
1. le dossier (JSON de l'Intake Agent) : les faits du sinistre ;
2. les conditions particulières du contrat de l'assuré : ce qui a été souscrit et déclaré
   (garanties souscrites, usage déclaré du véhicule, conducteurs désignés, date de souscription) ;
3. des extraits d'articles : le contrat (source: contrat) et le Code des assurances
   (source: code_assurances), qui indiquent les règles.
Tu dois dire si le sinistre est couvert : compare les faits du dossier aux conditions particulières,
puis applique les règles des articles fournis.

Règles :
- N'affirme rien qui ne soit pas fondé sur un article fourni ou sur les conditions particulières.
  Cite chaque article par son identifiant exact tel qu'il apparaît dans [Article ...] (ex. "15", "L113-2") ;
  pour un fait tiré des conditions particulières, écris "(conditions particulières)". N'utilise aucune
  autre connaissance.
- Une garantie qui ne figure pas dans les conditions particulières n'est pas souscrite.
- Cite d'abord les articles du contrat, puis ceux du Code des assurances. "articles_cites" ne contient
  que des identifiants d'articles fournis.
- Si les éléments fournis ne permettent pas de conclure, ou si un fait nécessaire manque dans le dossier,
  réponds "indetermine" et explique ce qui manque. Ne devine pas.
- "partiel" : le sinistre est couvert mais avec une limite (franchise majorée, garantie réduite,
  responsabilité partagée) qui réduit nettement l'indemnisation.
- Réponds UNIQUEMENT avec un objet JSON valide conforme au schéma ci-dessous, sans texte autour.

Schéma :
{
  "garantie_applicable": {"nom": "string", "article": "string"} | null,
  "exclusions_applicables": [{"article": "string", "motif": "string"}],
  "franchise": {"montant": "string | null", "article": "string | null", "detail": "string"} | null,
  "verdict_couverture": "couvert | non_couvert | partiel | indetermine",
  "articles_cites": ["string"],
  "justification": "3 à 6 phrases, chaque affirmation suivie de l'article ou de (conditions particulières) entre parenthèses",
  "confiance": "haute | moyenne | basse"
}"""


class GeminiError(Exception):
    def __init__(self, message, quota=False):
        super().__init__(message)
        self.quota = quota  # quota épuisé : inutile de lancer d'autres appels


def _nullable(schema):
    return {"anyOf": [schema, {"type": "null"}]}


# Schéma de sortie de P4 (même structure que dans PROMPT_P4), envoyé en sortie structurée
# (response_format json_schema, le mode JSON documenté pour l'endpoint compatible OpenAI).
SCHEMA_P4 = {
    "type": "object", "additionalProperties": False,
    "required": ["garantie_applicable", "exclusions_applicables", "franchise", "verdict_couverture",
                 "articles_cites", "justification", "confiance"],
    "properties": {
        "garantie_applicable": _nullable({"type": "object", "additionalProperties": False, "required": ["nom", "article"],
                                          "properties": {"nom": {"type": "string"}, "article": {"type": "string"}}}),
        "exclusions_applicables": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["article", "motif"],
            "properties": {"article": {"type": "string"}, "motif": {"type": "string"}}}},
        "franchise": _nullable({"type": "object", "additionalProperties": False, "required": ["montant", "article", "detail"],
                                "properties": {"montant": _nullable({"type": "string"}),
                                               "article": _nullable({"type": "string"}),
                                               "detail": {"type": "string"}}}),
        "verdict_couverture": {"type": "string", "enum": sorted(VERDICTS)},
        "articles_cites": {"type": "array", "items": {"type": "string"}},
        "justification": {"type": "string"},
        "confiance": {"type": "string", "enum": CONFIANCES},
    },
}


def fournisseur():
    """Fournisseur, URL de l'endpoint, modèle, clé API et timeout, d'après les variables d'environnement."""
    nom = os.environ.get("LLM_PROVIDER", "gemini").strip().lower() or "gemini"
    if nom == "gemini":
        return {"nom": nom, "url": GEMINI_URL, "modele": os.environ.get("GEMINI_MODEL", DEFAULT_MODEL),
                "cle": os.environ.get("GEMINI_API_KEY"), "timeout": TIMEOUT_S}
    if nom == "ollama":
        base = (os.environ.get("OLLAMA_BASE_URL") or OLLAMA_DEFAULT_URL).rstrip("/")
        base = base if base.endswith("/v1") else f"{base}/v1"
        return {"nom": nom, "url": f"{base}/chat/completions", "cle": None, "timeout": OLLAMA_TIMEOUT_S,
                "modele": os.environ.get("OLLAMA_POLICY_MODEL") or OLLAMA_DEFAULT_MODEL}
    raise GeminiError(f"LLM_PROVIDER inconnu : {nom!r} (gemini ou ollama)")


def _params(system, user, schema=None):
    """Paramètres de l'appel. Température 0 pour R1 et P4. Avec schema : sortie structurée
    (json_schema) ; sinon mode JSON simple (json_object). reasoning_effort pour Gemini seulement."""
    response_format = ({"type": "json_schema", "json_schema": {"name": "reponse", "strict": True, "schema": schema}}
                       if schema else {"type": "json_object"})
    f = fournisseur()
    params = {"model": f["modele"], "temperature": 0, "response_format": response_format,
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    effort = os.environ.get("GEMINI_REASONING_EFFORT", "low")
    if effort and f["nom"] == "gemini":
        params["reasoning_effort"] = effort
    return params


def cache_path(system, user, schema=None):
    """Fichier de cache d'un appel : hash du fournisseur, du modèle, du reasoning_effort, de la
    température, du response_format (schéma compris) et du prompt complet. Le fournisseur
    n'est ajouté que s'il n'est pas Gemini : les réponses Gemini déjà en cache restent valides."""
    p = _params(system, user, schema)
    cle = {k: p.get(k) for k in ("model", "reasoning_effort", "temperature", "response_format", "messages")}
    nom = fournisseur()["nom"]
    if nom != "gemini":
        cle["provider"] = nom
    cle = json.dumps(cle, ensure_ascii=False, sort_keys=True)
    return CACHE_DIR / f"{hashlib.sha256(cle.encode()).hexdigest()}.json"


def call_gemini(system, user, etape="", journal=None, cache=True, schema=None):
    """Appel du LLM (Gemini ou Ollama selon LLM_PROVIDER ; le nom est resté) en mode JSON.
    Renvoie le texte brut ; GeminiError en cas d'échec définitif, quel que soit le fournisseur.
    Chaque essai est ajouté à journal : {etape, essai, statut, duree_s} (statut « cache » si la
    réponse vient du cache disque)."""
    journal = journal if journal is not None else []
    fichier = cache_path(system, user, schema)
    if cache and fichier.exists():
        journal.append({"etape": etape, "essai": 0, "statut": "cache", "duree_s": 0.0})
        return json.loads(fichier.read_text(encoding="utf-8"))["content"]
    f = fournisseur()
    headers = {"Content-Type": "application/json"}
    if f["nom"] == "gemini":
        if not f["cle"]:
            raise GeminiError("GEMINI_API_KEY non défini")
        headers["Authorization"] = f"Bearer {f['cle']}"
    params = _params(system, user, schema)
    body = json.dumps(params)
    req = urllib.request.Request(f["url"], data=body.encode(), method="POST", headers=headers)
    intervalle = MIN_INTERVAL_S if f["nom"] == "gemini" else 0  # pas de quota en local
    last = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        attente = _dernier_appel[0] + intervalle - time.monotonic()
        if attente > 0:
            time.sleep(attente)
        _dernier_appel[0] = time.monotonic()
        t0 = time.perf_counter()

        def log(statut):
            journal.append({"etape": etape, "essai": attempt, "statut": statut,
                            "duree_s": round(time.perf_counter() - t0, 1)})
        try:
            with urllib.request.urlopen(req, timeout=f["timeout"]) as r:
                data = json.loads(r.read())
            content = data["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise GeminiError("réponse sans contenu texte")
            log("ok")
            CACHE_DIR.mkdir(exist_ok=True)
            fichier.write_text(json.dumps({"etape": etape, "fournisseur": f["nom"], "modele": params["model"],
                                           "reasoning_effort": params.get("reasoning_effort"),
                                           "date": time.strftime("%Y-%m-%d %H:%M:%S"), "content": content},
                                          ensure_ascii=False, indent=1), encoding="utf-8")
            return content
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            detail = e.read()[:2000].decode(errors="replace")
            quota = re.search(r"Quota exceeded for metric: [^\n\\\\]*", detail)
            log(f"{last} : {quota.group(0)}" if quota else last)  # 429 : le message dit quel quota
            if e.code not in RETRYABLE_HTTP:  # 400, 401, 403 : inutile de réessayer
                raise GeminiError(f"{last} : {detail}")
            wait = float(e.headers.get("Retry-After") or retry_delay(detail) or backoff(attempt))
            if wait > 60:  # quota journalier épuisé (« retry in 9h38m… ») : réessayer ne sert à rien
                raise GeminiError(f"{last} : quota épuisé, nouvel essai possible dans {wait / 3600:.1f} h",
                                  quota=True)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last, wait = f"réseau : {e}", backoff(attempt)
            log(last)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            log("réponse inattendue")
            raise GeminiError(f"réponse inattendue : {e!r}")
        if attempt < MAX_ATTEMPTS:
            time.sleep(min(wait, 60))
    raise GeminiError(f"échec après {MAX_ATTEMPTS} essais ({last})", quota=last == "HTTP 429")


def retry_delay(message):
    """Délai demandé par l'API dans le message d'erreur (« Please retry in 9h38m29.2s »), en secondes."""
    m = re.search(r"retry in ((?:\d+h)?(?:\d+m)?(?:[\d.]+s)?)", message)
    if not m or not m.group(1):
        return None
    parts = {unite: float(valeur) for valeur, unite in re.findall(r"([\d.]+)([hms])", m.group(1))}
    return parts.get("h", 0) * 3600 + parts.get("m", 0) * 60 + parts.get("s", 0)


def parse_json(text):
    """JSON du LLM, en tolérant un bloc ```json autour. None si invalide."""
    text = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text)
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def sous_questions(intake):
    """3 à 6 questions en langage courant, construites à partir des champs de l'intake.

    Avec conditions_particulieres.garanties, la question « garantie » nomme la garantie souscrite qui
    correspond au type de sinistre. Avec un tiers impliqué, la question « responsabilité » s'ajoute
    à la question « franchise ». La question « déclaration du risque » est posée quand l'usage au
    moment du sinistre diffère de l'usage déclaré, ou quand le conducteur n'est pas désigné.
    Au-delà de MAX_QUESTIONS, la question « délai de déclaration » est retirée en premier."""
    type_sinistre = intake.get("type_sinistre")
    t = TYPES.get(type_sinistre, "sinistre")
    circ = (intake.get("circonstances") or "").strip()
    tiers = intake.get("tiers_implique")
    avec_tiers = {True: " avec un tiers impliqué", False: " sans tiers impliqué"}.get(tiers, "")
    if type_sinistre == "sortie_de_route":
        avec_tiers = ""  # déjà dit par « sans autre véhicule »
    cp = intake.get("conditions_particulieres") or {}
    souscrites = cp.get("garanties")
    if souscrites is None:
        garantie = f"Quelle garantie couvre un sinistre de type {t}{avec_tiers} ?"
    else:
        candidates = [g for g in GARANTIES_PAR_TYPE.get(type_sinistre, []) if g in souscrites]
        if candidates:
            nom = NOMS_GARANTIES.get(candidates[0], candidates[0].replace("_", " "))
            garantie = f"La garantie {nom} couvre-t-elle un sinistre de type {t}{avec_tiers} ?"
        else:
            garantie = (f"Aucune garantie souscrite ne vise un sinistre de type {t} : "
                        f"la responsabilité civile ou une autre garantie du contrat s'applique-t-elle ?")
    qs = [("garantie", garantie),
          ("exclusions", f"Une exclusion de garantie s'applique-t-elle à ce sinistre ? Circonstances : {circ}"
           + (f" Usage du véhicule : {intake['usage_au_moment_du_sinistre']}."
              if intake.get("usage_au_moment_du_sinistre") else "")
           + (f" Usage déclaré au contrat : {cp['usage_declare']}." if cp.get("usage_declare") else ""))]
    qs.append(("franchise", f"Quelle franchise s'applique à un sinistre de type {t}{avec_tiers} ?"))
    if tiers:
        qs.append(("responsabilite", "Comment la responsabilité est-elle partagée entre les conducteurs d'après le "
                                     "constat amiable, et quelle franchise s'applique selon ce partage ?"))
    qs.append(("delai_declaration", f"Quel est le délai pour déclarer un sinistre de type {t} ?"))
    usage = (intake.get("usage_au_moment_du_sinistre") or "").strip().lower()
    declare = (cp.get("usage_declare") or "").strip().lower()
    usage_different = bool(usage and declare and usage not in declare)
    conducteur = (intake.get("conducteur") or "").strip().lower()
    designes = cp.get("conducteurs_designes")
    if designes is not None:
        autre = conducteur and conducteur not in {x.strip().lower() for x in designes}
        qui = "une personne qui n'est pas conducteur désigné au contrat"
    else:
        autre = conducteur and conducteur != (intake.get("souscripteur") or "").strip().lower()
        qui = "une autre personne que le souscripteur"
    if autre:
        qs.append(("conducteur", f"Le véhicule était conduit par {qui} : que prévoit le contrat pour ce "
                                 "conducteur (désignation, prêt du volant, ancienneté du permis) ?"))
    if usage_different or (autre and designes is not None):
        qs.append(("declaration_risque", "Quelles sont les conséquences d'une déclaration inexacte ou d'une omission "
                                         "dans la déclaration du risque, selon que l'assuré est de bonne foi ou non ?"))
    if len(qs) > MAX_QUESTIONS:
        qs = [q for q in qs if q[0] != "delai_declaration"][:MAX_QUESTIONS]
    return [{"id": i, "theme": th, "originale": q} for i, (th, q) in enumerate(qs, 1)]


def message_r1(questions):
    return json.dumps({"questions": [{"id": q["id"], "question": q["originale"]} for q in questions]},
                      ensure_ascii=False)


def reformuler(questions, avertissements, journal, etat, cache=True):
    try:
        obj = parse_json(call_gemini(PROMPT_R1, message_r1(questions), "reformulation", journal, cache))
    except GeminiError as e:
        etat["quota_epuise"] |= e.quota
        avertissements.append(f"Reformulation impossible ({e}) : recherche avec les questions d'origine seulement.")
        return questions
    by_id = {}
    for r in (obj or {}).get("reformulations", []):
        if isinstance(r, dict) and isinstance(r.get("reformulee"), str) and r["reformulee"].strip():
            by_id[r.get("id")] = r["reformulee"].strip()
    if not by_id:
        avertissements.append("Reformulation : JSON invalide ou vide, questions d'origine seulement.")
    return [{**q, "reformulee": by_id.get(q["id"])} for q in questions]


def retrouver_articles(questions):
    """Recherche pour chaque question (origine + reformulée), fusion par article, au plus MAX_ARTICLES :
    1. d'office, les PAR_RECHERCHE meilleurs articles de chaque recherche, par tours (le 1er de chaque
       recherche, puis le 2e), tant qu'il reste de la place : un article qu'une seule question
       trouve n'est plus évincé par ceux que plusieurs questions génériques remontent ;
    2. au moins MIN_ARTICLES_CONTRAT articles du contrat s'il y en a parmi les résultats, en
       remplaçant au besoin le moins bien classé des autres articles ;
    3. complément par somme des scores RRF."""
    from retriever import search
    articles, par_recherche = {}, []
    for q in questions:
        for texte in filter(None, (q["originale"], q.get("reformulee"))):
            ordre = []
            par_recherche.append(ordre)
            for hit in search(texte, k=K_PAR_QUESTION):
                if hit["metadata"]["article"] not in ordre:
                    ordre.append(hit["metadata"]["article"])
                m = hit["metadata"]
                a = articles.setdefault(m["article"], {"article": m["article"], "titre": m["titre"],
                                                       "source": m["source"], "score": 0.0,
                                                       "questions": set(), "parties": {}})
                a["score"] += hit["scores"]["rrf"]  # trouvé par plusieurs questions → mieux classé
                a["questions"].add(q["id"])
                partie = m.get("partie", 1)
                rrf = max(hit["scores"]["rrf"], a["parties"].get(partie, ("", 0))[1])
                a["parties"][partie] = (hit["text"], rrf)
    choisis = []  # identifiants d'articles, dans l'ordre d'ajout
    for tour in range(PAR_RECHERCHE):
        for ordre in par_recherche:
            if tour < len(ordre) and ordre[tour] not in choisis and len(choisis) < MAX_ARTICLES:
                choisis.append(ordre[tour])
                articles[ordre[tour]]["selection"] = f"d'office (rang {tour + 1} d'une recherche)"
    ranked = sorted(articles.values(), key=lambda a: -a["score"])
    for a in [a for a in ranked if a["source"] == "contrat" and a["article"] not in choisis]:
        if sum(articles[x]["source"] == "contrat" for x in choisis) >= MIN_ARTICLES_CONTRAT:
            break
        if len(choisis) >= MAX_ARTICLES:
            autres = [x for x in choisis if articles[x]["source"] != "contrat"]
            if not autres:
                break
            choisis.remove(min(autres, key=lambda x: articles[x]["score"]))
        choisis.append(a["article"])
        a["selection"] = "place réservée au contrat"
    for a in ranked:
        if len(choisis) >= MAX_ARTICLES:
            break
        if a["article"] not in choisis:
            choisis.append(a["article"])
            a["selection"] = "somme des scores RRF"
    best = sorted((articles[x] for x in choisis), key=lambda a: -a["score"])
    for a in best:
        a["questions"] = sorted(a["questions"])
        a["texte"] = "\n".join(a["parties"][p][0] for p in sorted(a["parties"]))
        a["meilleur_chunk"] = max(a["parties"].values(), key=lambda x: x[1])[0]
        a["nb_chunks"] = len(a["parties"])
        del a["parties"]
    return best


def prompt_p4(intake, fournis):
    """Message utilisateur de P4 et sa taille. Au-delà de MAX_PROMPT_TOKENS, chaque article
    est réduit à son chunk le mieux classé."""
    dossier = {k: v for k, v in intake.items() if k not in ("souscripteur", "conditions_particulieres")}
    cp = intake.get("conditions_particulieres")

    def construire(reduit):
        extraits = "\n\n".join(f"[Article {a['article']} — source: {a['source']} — {a['titre']}]\n"
                                f"{a['meilleur_chunk'] if reduit else a['texte']}" for a in fournis)
        return (f"## Dossier (faits du sinistre)\n{json.dumps(dossier, ensure_ascii=False, indent=1)}\n\n"
                f"## Conditions particulières (ce qui a été souscrit et déclaré)\n"
                f"{json.dumps(cp, ensure_ascii=False, indent=1) if cp else 'non fournies'}\n\n"
                f"## Articles fournis ({len(fournis)}, les règles)\n\n{extraits}")

    user = construire(False)
    taille = {"caracteres": len(PROMPT_P4) + len(user), "tokens_estimes": n_tokens(PROMPT_P4 + user),
              "reduit": False}
    if taille["tokens_estimes"] > MAX_PROMPT_TOKENS:
        avant = taille["tokens_estimes"]
        user = construire(True)
        taille = {"caracteres": len(PROMPT_P4) + len(user), "tokens_estimes": n_tokens(PROMPT_P4 + user),
                  "reduit": True, "tokens_avant_reduction": avant}
    return user, taille


def norm_article(x):
    """« Article L. 113-2 » → « L113-2 » ; « art. 15 » → « 15 »."""
    x = re.sub(r"^\s*(article|art\.?)\s*", "", str(x), flags=re.I)
    return re.sub(r"\s+|(?<=^[LRDA])\.\s*", "", x.strip()).replace("..", ".")


def baisser(confiance):
    i = CONFIANCES.index(confiance) if confiance in CONFIANCES else 1
    return CONFIANCES[min(i + 1, len(CONFIANCES) - 1)]


def indetermine(raison, **trace):
    return {"garantie_applicable": None, "exclusions_applicables": [], "franchise": None,
            "verdict_couverture": "indetermine", "articles_cites": [], "justification": raison,
            "confiance": "basse", **trace}


def controler(rep, fournis, avertissements):
    """Étape 5 : ne garder que les articles fournis ; contrat avant Code ; verdict valide."""
    sources = {a["article"]: a["source"] for a in fournis}
    retires = set()

    def valide(art):
        if art is None:
            return None
        n = norm_article(art)
        if n in sources:
            return n
        retires.add(str(art))
        return None

    rep["articles_cites"] = [n for n in (valide(a) for a in rep.get("articles_cites") or []) if n]
    rep["articles_cites"] = sorted(dict.fromkeys(rep["articles_cites"]),
                                   key=lambda a: sources[a] != "contrat")  # tri stable : contrat d'abord
    g = rep.get("garantie_applicable")
    if isinstance(g, dict):
        g["article"] = valide(g.get("article"))
    f = rep.get("franchise")
    if isinstance(f, dict):
        f["article"] = valide(f.get("article"))
    excl = []
    for e in rep.get("exclusions_applicables") or []:
        if isinstance(e, dict) and valide(e.get("article")):
            excl.append({**e, "article": norm_article(e["article"])})
    rep["exclusions_applicables"] = excl
    if rep.get("confiance") not in CONFIANCES:
        rep["confiance"] = "basse"
    if retires:
        rep["confiance"] = baisser(rep["confiance"])
        avertissements.append(f"Articles cités mais non fournis, retirés : {', '.join(sorted(retires))}.")
    if rep["verdict_couverture"] != "indetermine" and not rep["articles_cites"]:
        avertissements.append("Aucun article fourni n'est cité : verdict ramené à « indetermine ».")
        rep["verdict_couverture"], rep["confiance"] = "indetermine", "basse"
    return rep


def analyse_couverture(intake: dict, cache=True, reformulation=False) -> dict:
    """cache=False : nouvel appel même si la réponse est en cache. reformulation=True : les
    sous-questions sont aussi reformulées par R1 (deux appels au LLM au lieu d'un). Désactivée par
    défaut : aucun gain mesurable sur les 10 dossiers de test le 21/10/2026 (prompts/PROMPTS.md)."""
    avertissements, journal, etat = [], [], {"quota_epuise": False}
    try:
        f = fournisseur()
    except GeminiError as e:  # LLM_PROVIDER inconnu : inutile de lancer la recherche
        return indetermine(f"Analyse impossible : {e}.", trace={"avertissements": avertissements})
    questions = sous_questions(intake)
    if reformulation:
        questions = reformuler(questions, avertissements, journal, etat, cache)
    else:
        avertissements.append("Reformulation désactivée : recherche avec les questions d'origine seulement.")
    fournis = retrouver_articles(questions)
    trace = {"trace": {"fournisseur": f["nom"], "modele": f["modele"],
                       "reasoning_effort": (os.environ.get("GEMINI_REASONING_EFFORT", "low") or None)
                       if f["nom"] == "gemini" else None,
                       "reformulation": reformulation, "sous_questions": questions,
                       "articles_fournis": [{k: v for k, v in a.items() if k not in ("texte", "meilleur_chunk")}
                                            for a in fournis],
                       "appels": journal, "avertissements": avertissements, "quota_epuise": False}}
    if etat["quota_epuise"]:  # P4 échouerait aussi : on n'envoie pas de requête inutile
        trace["trace"]["quota_epuise"] = True
        return indetermine(f"Analyse impossible : quota {f['nom']} épuisé.", **trace)
    if not fournis:
        return indetermine("Aucun article retrouvé pour ce dossier.", **trace)

    user, trace["trace"]["prompt_p4"] = prompt_p4(intake, fournis)
    try:
        rep = parse_json(call_gemini(PROMPT_P4, user, "p4", journal, cache, schema=SCHEMA_P4))
    except GeminiError as e:
        trace["trace"]["quota_epuise"] = e.quota
        return indetermine(f"Analyse impossible : appel {f['nom']} en échec ({e}).", **trace)
    champs = {"garantie_applicable", "exclusions_applicables", "franchise", "verdict_couverture",
              "articles_cites", "justification", "confiance"}
    if rep is None or not champs <= rep.keys() or rep.get("verdict_couverture") not in VERDICTS:
        avertissements.append("Réponse P4 : JSON invalide ou incomplet.")
        return indetermine("Réponse du modèle invalide : couverture non déterminée.", **trace)
    return {**controler({k: rep[k] for k in champs}, fournis, avertissements), **trace}


# Résumés de test rédigés à la main, au format attendu de P1 (circonstances en 1 à 2 phrases
# neutres, usage extrait du texte) ; à remplacer par la vraie sortie de P1 quand elle sera testée.
INTAKE_TEST = {
    "D01": {"circonstances": "Véhicule arrêté au feu rouge, percuté à l'arrière par un autre véhicule dont le "
                             "conducteur a reconnu sa faute. Constat amiable rempli.",
            "zone_impact_declaree": "arriere"},
    "D02": {"circonstances": "Le véhicule a heurté un poteau en tournant, pendant une course VTC avec un client "
                             "à bord.",
            "usage_au_moment_du_sinistre": "transport de passager pour une application de VTC",
            "zone_impact_declaree": "avant"},
    "D07": {"circonstances": "Le fils du souscripteur, titulaire du permis depuis 1 an, a perdu le contrôle "
                             "du véhicule dans un virage sous la pluie et a fini dans le fossé.",
            "zone_impact_declaree": "lateral_droit"},
    "D03": {"circonstances": "Sur le parking d'un supermarché, un véhicule en marche arrière a heurté une portière "
                             "du véhicule assuré.",
            "zone_impact_declaree": "inconnue"},
    "D04": {"circonstances": "Collision frontale à un carrefour avec un véhicule qui n'a pas respecté la priorité ; "
                             "tout l'avant du véhicule assuré est endommagé.",
            "zone_impact_declaree": "avant"},
    "D05": {"circonstances": "Le véhicule a été rayé et son rétroviseur gauche cassé par un camion de livraison qui "
                             "a quitté les lieux ; l'assuré a relevé sa plaque d'immatriculation.",
            "zone_impact_declaree": "lateral_gauche"},
    "D06": {"circonstances": "Le véhicule a été volé devant le domicile de l'assuré dans la nuit du 1er au "
                             "2 octobre 2026.",
            "zone_impact_declaree": "inconnue"},
    "D08": {"circonstances": "Un gravillon a frappé le pare-brise sur l'autoroute ; la fissure s'est agrandie "
                             "pendant la nuit et le pare-brise doit être remplacé.",
            "zone_impact_declaree": "vitrage"},
    "D09": {"circonstances": "Au retour de vacances, l'assuré a constaté une vitre cassée et l'autoradio arraché.",
            "zone_impact_declaree": "vitrage",
            "remarques": ["Date de déclaration indiquée au formulaire : 2026-10-01."]},
    "D10": {"circonstances": "Un petit impact sur le pare-brise a été réparé par le garage sans remplacement.",
            "zone_impact_declaree": "vitrage"},
}


def intake_depuis_dossier(d, conditions_particulieres=None):
    """Intake simple construit à partir d'un dossier synthétique, en attendant P1."""
    f = d.get("formulaire") or {}
    intake = {"date_sinistre": f.get("date_sinistre"), "heure": None, "lieu": (d.get("constat") or {}).get("lieu"),
              "type_sinistre": f.get("type"), "tiers_implique": f.get("tiers_implique"),
              "conducteur": f.get("conducteur") or f.get("nom"), "souscripteur": f.get("nom"),
              "circonstances": d.get("declaration"), "zone_impact_declaree": None,
              "usage_au_moment_du_sinistre": None, "ecarts_formulaire": [], "remarques": [],
              "conditions_particulieres": conditions_particulieres}
    return {**intake, **INTAKE_TEST.get(d["id"], {})}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("dossiers", nargs="*", default=["D01"])
    ap.add_argument("--sans-cache", action="store_true", help="nouvel appel au LLM même si la réponse est en cache")
    ap.add_argument("--avec-reformulation", action="store_true", help="active la reformulation R1 (désactivée par défaut)")
    args = ap.parse_args()
    data = json.loads((ROOT / "data/dossiers/dossiers_synthetiques.json").read_text(encoding="utf-8"))
    cp = data["contrat_reference"]
    for did in args.dossiers:
        d = next(x for x in data["dossiers"] if x["id"] == did)
        print(f"\n===== {did} — {d['scenario']} (attendu : {d['attendu']}) =====")
        print(json.dumps(analyse_couverture(intake_depuis_dossier(d, cp), cache=not args.sans_cache,
                                            reformulation=args.avec_reformulation), ensure_ascii=False, indent=2))
