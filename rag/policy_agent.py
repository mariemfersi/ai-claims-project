"""Policy Agent v1 : analyse de couverture d'un dossier à partir du JSON de l'Intake Agent.

Usage :
    python rag/policy_agent.py D01 D02 D07     # test sur des dossiers synthétiques

    from policy_agent import analyse_couverture
    resultat = analyse_couverture(intake)

Étapes :
1. 3 à 5 sous-questions déterministes à partir du dossier (garantie, exclusions,
   franchise, délai de déclaration, conducteur si ce n'est pas le souscripteur).
2. Reformulation par Gemini dans le vocabulaire du contrat et du Code (prompt R1,
   prompts/PROMPTS.md). En cas d'échec, on garde les questions d'origine.
3. retriever.search(k=5) sur chaque question (origine + reformulée) ; fusion par
   article (somme des scores RRF), au plus 8 articles.
4. Réponse de couverture par Gemini (prompt P4), en JSON uniquement.
5. Contrôle : un article cité qui n'a pas été fourni est retiré et la confiance baisse ;
   JSON invalide, aucun article valide ou erreur d'appel → verdict « indetermine ».

Configuration : GEMINI_API_KEY (obligatoire, jamais dans le code), GEMINI_MODEL
(défaut : gemini-3.8-flash, modèle stable de la documentation Gemini en octobre 2026).
Appel via l'endpoint compatible OpenAI, comme le workflow n8n.

Extension du schéma P1 : un champ optionnel « souscripteur » permet de savoir si le
conducteur est une autre personne ; sans lui, la question conducteur n'est posée que
si l'intake mentionne un conducteur.
"""
import json, os, re, sys, time, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
DEFAULT_MODEL = "gemini-3.8-flash"
MAX_ATTEMPTS = 3          # 1 appel + 2 nouveaux essais
RETRYABLE_HTTP = {429, 500, 502, 503, 504}
K_PAR_QUESTION = 5
MAX_ARTICLES = 8
VERDICTS = {"couvert", "non_couvert", "partiel", "indetermine"}
CONFIANCES = ["haute", "moyenne", "basse"]

TYPES = {"collision": "collision", "sortie_de_route": "sortie de route sans autre véhicule", "vol": "vol",
         "tentative_vol": "tentative de vol", "bris_de_glace": "bris de glace", "incendie": "incendie",
         "climatique": "événement climatique", "autre": "autre sinistre"}

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
On te donne un dossier (JSON de l'Intake Agent) et des extraits d'articles : le contrat de l'assuré
(source: contrat) et le Code des assurances (source: code_assurances).
Tu dois dire si le sinistre est couvert, en t'appuyant uniquement sur ces extraits.

Règles :
- N'affirme rien qui ne soit pas fondé sur un article fourni, et cite cet article par son identifiant
  exact tel qu'il apparaît dans [Article ...] (ex. "15", "L113-2"). N'utilise aucune autre connaissance.
- Cite d'abord les articles du contrat, puis ceux du Code des assurances.
- Si les extraits ne permettent pas de conclure, ou si un fait nécessaire manque dans le dossier,
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
  "justification": "3 à 6 phrases, chaque affirmation suivie de l'article entre parenthèses",
  "confiance": "haute | moyenne | basse"
}"""


class GeminiError(Exception):
    pass


def call_gemini(system, user):
    """Appel Gemini en mode JSON. Renvoie le texte brut ; GeminiError en cas d'échec définitif."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise GeminiError("GEMINI_API_KEY non défini")
    body = json.dumps({"model": os.environ.get("GEMINI_MODEL", DEFAULT_MODEL), "temperature": 0,
                       "response_format": {"type": "json_object"},
                       "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
    req = urllib.request.Request(GEMINI_URL, data=body.encode(), method="POST",
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    last = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read())
            content = data["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise GeminiError("réponse sans contenu texte")
            return content
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code not in RETRYABLE_HTTP:  # 400, 401, 403 : inutile de réessayer
                raise GeminiError(f"{last} : {e.read()[:300].decode(errors='replace')}")
            wait = float(e.headers.get("Retry-After") or 2 ** attempt)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last, wait = f"réseau : {e}", 2 ** attempt
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise GeminiError(f"réponse inattendue : {e!r}")
        if attempt < MAX_ATTEMPTS:
            time.sleep(min(wait, 30))
    raise GeminiError(f"échec après {MAX_ATTEMPTS} essais ({last})")


def parse_json(text):
    """JSON du LLM, en tolérant un bloc ```json autour. None si invalide."""
    text = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text)
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def sous_questions(intake):
    """3 à 5 questions en langage courant, construites à partir des champs de l'intake."""
    t = TYPES.get(intake.get("type_sinistre"), "sinistre")
    circ = (intake.get("circonstances") or "").strip()
    tiers = intake.get("tiers_implique")
    avec_tiers = {True: "avec un tiers impliqué", False: "sans tiers impliqué"}.get(tiers, "")
    qs = [("garantie", f"Quelle garantie couvre un sinistre de type {t} ? Circonstances : {circ}".strip()),
          ("exclusions", f"Une exclusion de garantie s'applique-t-elle à ce sinistre ? Circonstances : {circ}"
           + (f" Usage du véhicule : {intake['usage_au_moment_du_sinistre']}."
              if intake.get("usage_au_moment_du_sinistre") else "")),
          ("franchise", f"Quelle franchise s'applique à un sinistre de type {t} {avec_tiers} ?".replace("  ", " ")),
          ("delai_declaration", f"Quel est le délai pour déclarer un sinistre de type {t} ?")]
    conducteur, souscripteur = intake.get("conducteur"), intake.get("souscripteur")
    if conducteur and (not souscripteur or conducteur.strip().lower() != souscripteur.strip().lower()):
        qs.append(("conducteur", "Le véhicule était conduit par une autre personne que le souscripteur : "
                                 "que prévoit le contrat pour ce conducteur (désignation, prêt du volant, "
                                 "ancienneté du permis) ?"))
    return [{"id": i, "theme": th, "originale": q} for i, (th, q) in enumerate(qs, 1)]


def reformuler(questions, avertissements):
    user = json.dumps({"questions": [{"id": q["id"], "question": q["originale"]} for q in questions]},
                      ensure_ascii=False)
    try:
        obj = parse_json(call_gemini(PROMPT_R1, user))
    except GeminiError as e:
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
    """Recherche pour chaque question (origine + reformulée), fusion par article."""
    from retriever import search
    articles = {}
    for q in questions:
        for texte in filter(None, (q["originale"], q.get("reformulee"))):
            for hit in search(texte, k=K_PAR_QUESTION):
                m = hit["metadata"]
                a = articles.setdefault(m["article"], {"article": m["article"], "titre": m["titre"],
                                                       "source": m["source"], "score": 0.0,
                                                       "questions": set(), "parties": {}})
                a["score"] += hit["scores"]["rrf"]  # trouvé par plusieurs questions → mieux classé
                a["questions"].add(q["id"])
                a["parties"][m.get("partie", 1)] = hit["text"]
    best = sorted(articles.values(), key=lambda a: -a["score"])[:MAX_ARTICLES]
    for a in best:
        a["questions"] = sorted(a["questions"])
        a["texte"] = "\n".join(a["parties"][p] for p in sorted(a["parties"]))
        del a["parties"]
    return best


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


def analyse_couverture(intake: dict) -> dict:
    avertissements = []
    questions = reformuler(sous_questions(intake), avertissements)
    fournis = retrouver_articles(questions)
    trace = {"trace": {"modele": os.environ.get("GEMINI_MODEL", DEFAULT_MODEL), "sous_questions": questions,
                       "articles_fournis": [{k: v for k, v in a.items() if k != "texte"} for a in fournis],
                       "avertissements": avertissements}}
    if not fournis:
        return indetermine("Aucun article retrouvé pour ce dossier.", **trace)

    extraits = "\n\n".join(f"[Article {a['article']} — source: {a['source']} — {a['titre']}]\n{a['texte']}"
                           for a in fournis)
    dossier = {k: v for k, v in intake.items() if k != "souscripteur"}
    user = (f"Dossier :\n{json.dumps(dossier, ensure_ascii=False, indent=1)}\n\n"
            f"Articles fournis ({len(fournis)}) :\n\n{extraits}")
    try:
        rep = parse_json(call_gemini(PROMPT_P4, user))
    except GeminiError as e:
        return indetermine(f"Analyse impossible : appel Gemini en échec ({e}).", **trace)
    champs = {"garantie_applicable", "exclusions_applicables", "franchise", "verdict_couverture",
              "articles_cites", "justification", "confiance"}
    if rep is None or not champs <= rep.keys() or rep.get("verdict_couverture") not in VERDICTS:
        avertissements.append("Réponse P4 : JSON invalide ou incomplet.")
        return indetermine("Réponse du modèle invalide : couverture non déterminée.", **trace)
    return {**controler({k: rep[k] for k in champs}, fournis, avertissements), **trace}


def intake_depuis_dossier(d):
    """Intake simple construit à partir des champs d'un dossier synthétique (en attendant P1)."""
    f = d.get("formulaire") or {}
    return {"date_sinistre": f.get("date_sinistre"), "heure": None, "lieu": (d.get("constat") or {}).get("lieu"),
            "type_sinistre": f.get("type"), "tiers_implique": f.get("tiers_implique"),
            "conducteur": f.get("conducteur") or f.get("nom"), "souscripteur": f.get("nom"),
            "circonstances": d.get("declaration"), "zone_impact_declaree": None,
            "usage_au_moment_du_sinistre": None, "ecarts_formulaire": [], "remarques": []}


if __name__ == "__main__":
    data = json.loads((ROOT / "data/dossiers/dossiers_synthetiques.json").read_text(encoding="utf-8"))
    for did in sys.argv[1:] or ["D01"]:
        d = next(x for x in data["dossiers"] if x["id"] == did)
        print(f"\n===== {did} — {d['scenario']} (attendu : {d['attendu']}) =====")
        print(json.dumps(analyse_couverture(intake_depuis_dossier(d)), ensure_ascii=False, indent=2))
