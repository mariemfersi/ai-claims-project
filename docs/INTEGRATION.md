# Intégrer le Policy Agent RAG dans la branche `ines`

Ce guide permet d'intégrer le Policy Agent de la branche `ragAgent` dans le backend Django de la branche `ines`,
sans l'auteur. Les chemins `backend/...`, `frontend/...` et `docker-compose.yml` sont ceux de `ines` (état du
27 octobre 2026, commit `a2a5d62`) ; les chemins `rag/...`, `data/...` et `results/...` sont ceux de `ragAgent`.

Sommaire : [1. Résumé](#1-résumé) · [2. Fichiers à copier](#2-fichiers-à-copier) ·
[3. Changement dans agents.py](#3-changement-dans-backendclaimsagentspy) ·
[4. Correspondance des verdicts](#4-correspondance-des-verdicts) · [5. Configuration du LLM](#5-configuration-du-llm) ·
[6. Dépendances](#6-dépendances) · [7. Qdrant et docker-compose](#7-qdrant-et-docker-composeyml) ·
[8. Indexation du corpus](#8-indexation-du-corpus) · [9. Points à décider](#9-points-à-décider-ou-à-modifier-par-léquipe) ·
[10. Limites connues](#10-limites-connues)

---

## 1. Résumé

L'agent répond à la question : **le sinistre est-il couvert par le contrat, et selon quels articles ?**

1. Il construit 3 à 6 sous-questions à partir du dossier (garantie, exclusions, franchise, responsabilité si un tiers
   est impliqué, délai de déclaration, conducteur, déclaration du risque).
2. Pour chacune, il cherche les articles pertinents dans un corpus de **594 chunks** : le contrat (26 articles) et
   des extraits du Code des assurances (415 articles). La recherche est hybride : BM25 racinisé + embeddings
   `BAAI/bge-m3` dans Qdrant, fusionnés par RRF. Au plus 10 articles sont retenus.
3. Le LLM (Gemini ou un modèle local via Ollama) reçoit le dossier, les conditions particulières et les articles,
   et répond en JSON contraint par un schéma : verdict (`couvert`, `non_couvert`, `partiel`, `indetermine`),
   garantie, exclusions, franchise, articles cités, justification.
4. Le code vérifie la réponse : un article cité mais non fourni est retiré, et sans article valide le verdict
   devient `indetermine`.

L'adaptateur `rag/integration.py` renvoie exactement les clés du `policy_agent(claim)` actuel de
`backend/claims/agents.py`, plus `verdict_couverture`, `articles_cites`, `franchise` et `trace`. Il ne lève jamais
d'exception : en cas de panne (Qdrant, LLM, import), il renvoie `insufficient_information` avec une explication et
le type d'erreur dans `diagnostic_error`.

**Résultats d'évaluation** :

| Évaluation | Résultat | Détail |
|---|---|---|
| Retrieval (32 requêtes) | MRR@5 = 0,79 ; hit@5 = 0,91 | [results/SYNTHESE_RAG.md](../results/SYNTHESE_RAG.md) |
| Agent complet, Gemini `gemini-3.5-flash-lite` (10 dossiers, 2 lancements) | 7/10 et 6/10 verdicts corrects, 0 refus à tort | [results/eval_policy_agent.md](../results/eval_policy_agent.md), section Analyse |
| Agent complet, Ollama `qwen2.5:7b` (10 dossiers) | 6/10 verdicts corrects, 0 refus à tort | idem |
| Agent complet, Ollama `qwen2.5:3b` (10 dossiers) | 4/10 verdicts corrects, **5 refus à tort** | idem |

Comparaison détaillée des trois modèles : [section 5](#5-configuration-du-llm).

---

## 2. Fichiers à copier

L'image Docker du backend est construite depuis `backend/` (`build: ./backend`, `WORKDIR /app`, `COPY . .`). En
développement, `docker-compose.yml` monte aussi `./backend` sur `/app`. Les fichiers vont donc **sous `backend/`** :

| Depuis `ragAgent` | Vers `ines` | Rôle |
|---|---|---|
| `rag/integration.py` | `backend/rag/integration.py` | adaptateur appelé par Django |
| `rag/policy_agent.py` | `backend/rag/policy_agent.py` | sous-questions, recherche, appel au LLM, contrôle |
| `rag/retriever.py` | `backend/rag/retriever.py` | recherche hybride (Qdrant + BM25) |
| `rag/index_qdrant.py` | `backend/rag/index_qdrant.py` | indexation, client Qdrant (`QDRANT_URL`) |
| `rag/eval_retrieval.py` | `backend/rag/eval_retrieval.py` | requis : `BM25` et `DEFAULT_MODEL` y sont définis |
| `rag/chunking.py` | `backend/rag/chunking.py` | découpage du corpus par article |
| `data/corpus/conditions_generales_auto.md` | `backend/data/corpus/` | contrat |
| `data/corpus/code_assurances_extraits.md` | `backend/data/corpus/` | Code des assurances |
| `rag/test_integration.py`, `rag/test_llm_provider.py`, `rag/test_qdrant_url.py` | `backend/rag/` | facultatif : tests sans LLM ni Qdrant |

Les modules calculent leur racine avec `Path(__file__).resolve().parent.parent`. Placés dans `backend/rag/`, ils
lisent donc le corpus dans `backend/data/corpus/` et écrivent le cache des réponses du LLM dans
`backend/cache_llm/`. Il ne faut pas changer cette disposition.

Commande (Git Bash, à la racine d'un clone sur la branche `ines`) :

```bash
git fetch origin ragAgent
git archive origin/ragAgent rag/integration.py rag/policy_agent.py rag/retriever.py rag/index_qdrant.py \
    rag/eval_retrieval.py rag/chunking.py rag/test_integration.py rag/test_llm_provider.py rag/test_qdrant_url.py \
    data/corpus | tar -x -C backend
touch backend/rag/__init__.py
printf 'backend/cache_llm/\nbackend/qdrant_db/\n' >> .gitignore
```

Ne pas copier `qdrant_db/` (index local, reconstruit à la [section 8](#8-indexation-du-corpus)), `cache_llm/`,
`demo/` ni `results/`.

Vérification sans LLM ni Qdrant (dans le conteneur ou en local) :

```bash
cd backend && python rag/test_integration.py && python rag/test_llm_provider.py && python rag/test_qdrant_url.py
```

---

## 3. Changement dans `backend/claims/agents.py`

Le principe : renommer la fonction actuelle (ligne 326) en `_policy_agent_legacy`, et la remplacer par une fonction qui
appelle l'adaptateur. `POLICY_ENGINE=legacy` permet de revenir à l'ancienne version sans toucher au code.

**a. `backend/config/settings.py`**, à côté des variables `OLLAMA_*` :

```python
POLICY_ENGINE = os.getenv("POLICY_ENGINE", "rag")  # rag (branche ragAgent) ou legacy (version précédente)
```

**b. `backend/claims/agents.py`** : renommer `def policy_agent(claim):` en `def _policy_agent_legacy(claim):` sans
toucher à son corps, puis coller juste en dessous :

```python
def policy_agent(claim):
    """Policy Agent RAG (rag/integration.py) ; POLICY_ENGINE=legacy pour la version précédente."""
    if settings.POLICY_ENGINE == "legacy":
        return _policy_agent_legacy(claim)
    from rag.integration import policy_agent_pour_backend
    return policy_agent_pour_backend({
        "customer_name": claim.customer_name,
        "policy_number": claim.policy_number,
        "description": claim.description,
        "incident_date": claim.incident_date,
        "location": claim.location,
        # Champs facultatifs, à remplir quand ils existeront dans le modèle Claim (section 9)
        "type_sinistre": getattr(claim, "type_sinistre", None),
        "conditions_particulieres": getattr(claim, "conditions_particulieres", None),
    })
```

Rien d'autre à changer : `backend/claims/views.py` importe déjà `policy_agent` (ligne 10), et `run_policy_agent`
l'appelle via `_execute_agent(claim.id, "policy", policy_agent, claim)`. `fraud_agent` et `decision_agent` lisent
`coverage_status`, `explanation` et `references`, que l'adaptateur fournit.

**Entrée de l'adaptateur** (`policy_agent_pour_backend(claim: dict)`) : les champs du modèle `Claim`, `incident_date`
en `date` ou en texte ISO. Facultatifs : `conditions_particulieres`, `type_sinistre`, `tiers_implique`, `conducteur`,
`usage_au_moment_du_sinistre`. Sans `type_sinistre`, il est déduit de la description par mots-clés.

**Sortie** : les 12 clés de l'ancien `policy_agent` (`agent`, `engine`, `model`, `embedding_model`,
`coverage_status`, `references`, `retrieved_chunks`, `retrieval_query`, `explanation`, `missing_information`,
`confidence`, `diagnostic_error`), plus `verdict_couverture`, `articles_cites`, `franchise` et `trace` (sous-questions,
articles fournis, appels au LLM, avertissements). Chaque élément de `references` contient
`{page, section, source, text, article}`. `section` vaut par exemple « Article 7 — Dommages collision », et `source`
vaut « Contrat » ou « Code des assurances ».

**Première requête** : le premier appel charge `bge-m3`, l'index BM25 et le client Qdrant (~13 s mesurées sur CPU,
modèle déjà téléchargé). Les appels suivants réutilisent ce chargement dans le même processus.

---

## 4. Correspondance des verdicts

| `verdict_couverture` (agent) | `coverage_status` (backend) | Décision produite par `decision_agent` |
|---|---|---|
| `couvert` | `covered` | ACCEPT si aucun risque de fraude, sinon INVESTIGATE |
| `non_couvert` | `excluded` | REJECT |
| `partiel` | `insufficient_information` | INVESTIGATE |
| `indetermine` | `insufficient_information` | INVESTIGATE |

**Pourquoi `partiel` donne `insufficient_information`** : dans `decision_agent` (lignes 385 à 398 de `agents.py`),
`covered` sans risque de fraude devient un **ACCEPT automatique**. Une couverture partielle (franchise majorée,
garantie réduite, responsabilité partagée) doit être examinée par un gestionnaire. L'explication commence alors par
« Couverture partielle : », et `verdict_couverture` garde la valeur `partiel`.

`confidence` : haute → 0,9 ; moyenne → 0,6 ; basse → 0,3.

---

## 5. Configuration du LLM

Le fournisseur se choisit par variables d'environnement (fichier `.env` du backend), sans changer le code. Les deux
fournisseurs passent par l'endpoint compatible OpenAI.

| Variable | Valeur | Rôle |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | Modèle local. **À définir** : la valeur par défaut est `gemini`. |
| `LLM_PROVIDER` | `gemini` | Avec `GEMINI_API_KEY` (obligatoire), `GEMINI_MODEL` (défaut `gemini-3.8-flash`), `GEMINI_REASONING_EFFORT` (défaut `low`). |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Déjà dans `.env.example`. Le code ajoute `/v1`. |
| `OLLAMA_POLICY_MODEL` | **`qwen2.5:7b`** | Recommandé. `.env.example` contient `qwen2.5:3b`, déconseillé (voir ci-dessous). Cette variable est aussi lue par `_policy_agent_legacy`. |
| `OLLAMA_CONTEXT_LENGTH` | **`8192`** | **Obligatoire**, à définir sur le **serveur Ollama** (la machine hôte), pas dans `.env`. |
| `POLICY_ENGINE` | `rag` | `legacy` : retour à l'ancien `policy_agent`. |

`OLLAMA_ENABLED` et `AI_REQUEST_TIMEOUT` ne sont pas lus par l'agent RAG. Il a ses propres délais maximaux : 600 s par
appel Ollama (120 s pour Gemini), avec 3 essais en cas d'erreur réseau ou serveur.

**`qwen2.5:7b` recommandé en local** : aucun refus à tort sur les 10 dossiers, articles cités proches de ceux de
Gemini, ~14 s par appel sur un GPU portable de 6 Go (RTX 4050).

**`qwen2.5:3b` déconseillé pour le Policy Agent** : 5 refus à tort sur 10, parce qu'il invente des exclusions. Il
applique « usage non déclaré » dans 7 dossiers où rien ne l'établit, et transforme l'absence d'une information en
exclusion. Extraits de ses justifications (`results/eval_policy_agent_ollama_3b.json`) :

- D10 (bris de glace simple) : « les conditions particulières indiquent que le véhicule est utilisé pour un usage
  non déclaré (transport de personnes), ce qui entraîne une exclusion ». Rien de tel dans le dossier ni dans les
  conditions particulières.
- D01 (sinistre simple, à accepter) : « Le conducteur Sami Ben Salah n'est pas mentionné comme titulaire d'un permis
  de conduire en état de validité, ce qui constitue une exclusion. »
- D05 : « la garantie dommages tous accidents ne couvre pas les dommages subis par le véhicule lui-même
  (Article 7) », alors que c'est précisément son objet.

Avec l'adaptateur, « non_couvert » devient `excluded`, puis un REJECT automatique.

**`OLLAMA_CONTEXT_LENGTH=8192` obligatoire** : par défaut, Ollama charge le modèle avec une fenêtre de 4 096 tokens
(documentation Ollama, FAQ). Un prompt plus long est tronqué côté serveur, sans erreur renvoyée au client. Le journal
du serveur l'indique par `truncated = 1`. Nos appels (prompt P4 et réponse) atteignent déjà ~4 000 tokens (3 981 au
maximum sur le jeu de test), et le code autorise des prompts jusqu'à ~6 000 tokens. Réglage selon la documentation
Ollama :

- **Windows** : quitter Ollama, ajouter la variable d'environnement utilisateur `OLLAMA_CONTEXT_LENGTH=8192`,
  relancer Ollama.
- **Linux (systemd)** : `systemctl edit ollama.service`, ajouter `Environment="OLLAMA_CONTEXT_LENGTH=8192"` sous
  `[Service]`, puis `systemctl daemon-reload && systemctl restart ollama`.
- **Vérification** : `ollama ps` doit afficher `8192` dans la colonne CONTEXT une fois le modèle chargé.

**Gemini reste le meilleur pour relever les réserves**, si un appel externe est acceptable. C'est le seul modèle qui
signale les conditions à vérifier, par exemple la plainte et les traces d'effraction pour un vol (D06, dans ses
deux lancements). Un appel dure ~2 s. En contrepartie : quota de l'offre gratuite (13 s imposées entre deux appels)
et données du dossier envoyées à un service externe.

### Comparaison sur les 10 dossiers synthétiques

Même code (sans reformulation, température 0, sortie structurée), mêmes articles fournis au LLM pour les trois
modèles : seul le raisonnement change.

| Métrique | `gemini-3.5-flash-lite` (lancements 1 ; 2) | `qwen2.5:3b` | `qwen2.5:7b` |
|---|---|---|---|
| Verdicts corrects | 7/10 ; 6/10 | 4/10, dont 3 pour une mauvaise raison | 6/10 |
| Refus à tort (REJECT automatique) | 0 ; 0 | **5** | 0 |
| Rappel périmètre couverture | 83 % ; 71 % | 42 % | 77 % |
| Précision des articles | 53 % ; 57 % | 24 % | 60 % |
| Réponses JSON invalides | 0 ; 0 | 0 | 0 |
| Durée moyenne par dossier | 13,9 s ; 12,8 s | 11,5 s | 16,2 s |
| dont appel au LLM | 4,3 s ; 2,0 s | 9,7 s | 14,0 s |

Pour Gemini, la durée par dossier vient surtout de l'attente imposée par le quota gratuit. Les modèles Ollama ont
tourné entièrement sur le GPU.

> **Mise en garde** : un seul lancement par modèle local, sur 10 dossiers. Deux lancements Gemini identiques
> diffèrent déjà sur 3 dossiers : l'écart d'un dossier entre Gemini et `qwen2.5:7b` ne permet pas de conclure.
> L'écart avec `qwen2.5:3b` est d'une autre nature : il se lit dans les justifications (exclusions inventées), pas
> seulement dans les scores.

---

## 6. Dépendances

À ajouter à `backend/requirements.txt`. Ce sont les versions installées et testées sur `ragAgent` (le
`requirements.txt` de `ragAgent` ne fixe pas de versions). Elles ont été testées sous Python 3.11 ; l'image du
backend est en `python:3.12-slim`, pour laquelle les roues existent mais n'ont pas été testées.

```text
# Policy Agent RAG (branche ragAgent)
--extra-index-url https://download.pytorch.org/whl/cpu
torch==2.14.1+cpu
sentence-transformers==6.1.0
transformers==5.19.0
qdrant-client==1.19.1
rank-bm25==0.2.2
snowballstemmer==3.1.1
tiktoken==0.14.0
numpy==2.4.6
```

`torch` en version CPU évite de télécharger la version CUDA, de plusieurs gigaoctets, que `pip` installe par défaut
sous Linux (`torch-2.14.1+cpu` existe pour cp312 / manylinux x86_64). L'agent n'a pas besoin de `requests` ni
d'autre client HTTP : les appels au LLM utilisent `urllib` de la bibliothèque standard.

Téléchargements au premier usage, qui demandent un accès Internet : le modèle `BAAI/bge-m3` (~2,3 Go, dans
`HF_HOME`) et l'encodage `cl100k_base` de `tiktoken` (dans `TIKTOKEN_CACHE_DIR`). La [section 7](#7-qdrant-et-docker-composeyml)
les place dans un volume.

---

## 7. Qdrant et `docker-compose.yml`

**a. Service à ajouter** sous `services:` :

```yaml
  qdrant:
    image: qdrant/qdrant:v1.19.2   # même version mineure que qdrant-client 1.19.1
    volumes:
      - qdrant_data:/qdrant/storage
    ports:
      - "6333:6333"                # facultatif : accès depuis l'hôte (tableau de bord, index_qdrant.py en local)
```

**b. Dans le service `backend`**, ajouter :

```yaml
    environment:
      QDRANT_URL: http://qdrant:6333
      HF_HOME: /models/huggingface
      TIKTOKEN_CACHE_DIR: /models/tiktoken
    volumes:
      # à ajouter aux volumes existants
      - embedding_models:/models
    depends_on:
      # à ajouter à la condition existante sur db
      qdrant:
        condition: service_started
```

**c. Sous `volumes:`** (fin du fichier) :

```yaml
  qdrant_data:
  embedding_models:
```

`QDRANT_URL` est lu par `rag/index_qdrant.py:get_client`, qu'utilisent l'indexation et la recherche. Sans cette
variable, le client ouvre un index local dans `backend/qdrant_db/`. Ce mode marche aussi, mais un seul processus à la
fois peut ouvrir ce dossier : à éviter dès qu'il y a plusieurs workers. Les variables d'environnement peuvent aussi
aller dans `.env`, que le service `backend` lit déjà (`env_file: .env`).

**Mémoire** : le processus backend occupe **~2,0 Go** de RAM après le chargement de `bge-m3`, de l'index BM25 et
d'une recherche, sur CPU. Cette mesure est faite en mode Qdrant local ; avec le service Qdrant, l'index est dans
l'autre conteneur. Ces ~2 Go s'ajoutent à Whisper et à Django, et chaque processus qui appelle l'agent (worker)
charge son propre modèle. Le pic pendant l'indexation n'a pas été mesuré. Prévoir **au moins 4 Go** pour le
conteneur backend (Docker Desktop : Settings → Resources). Le service Qdrant ne stocke que 594 vecteurs : quelques
dizaines de Mo.

---

## 8. Indexation du corpus

À lancer **une fois** après le premier `docker compose up`, puis après chaque modification de
`backend/data/corpus/` :

```bash
docker compose exec backend python rag/index_qdrant.py
```

Le script télécharge `bge-m3` dans le volume au premier lancement. Il encode les 594 chunks (**~5 min sur CPU**,
mesure de `rag/eval_retrieval.py`), puis supprime et recrée la collection `corpus_assurance` : le relancer donne
toujours le même index. Il affiche le nombre de points (594 attendus).

Vérification rapide de la recherche :

```bash
docker compose exec backend python rag/retriever.py "Le bris de glace est-il couvert ?"
```

---

## 9. Points à décider ou à modifier par l'équipe

1. **« Page ? » dans l'interface.** Le corpus est découpé par article, pas par page : `page` vaut `None`.
   `frontend/src/App.jsx` affiche toujours `Page {ref.page || "?"}` (lignes 281 et 410), donc « Page ? ·
   Article 7 — Dommages collision ». Proposition, aux deux endroits :
   `{ref.page ? `Page ${ref.page} · ` : ""}{ref.section || ref.source}`.

2. **Type de sinistre et conditions particulières.** Le modèle `Claim` (`backend/claims/models.py`) n'a pas ces
   champs. Sans eux, le type est deviné par mots-clés, et l'agent ne sait pas ce qui a été souscrit :
   `missing_information` contient alors « Conditions particulières et garanties souscrites », et le prompt considère
   comme non souscrite une garantie absente des conditions particulières. Cette configuration n'a pas été évaluée,
   car les 10 dossiers de test ont tous des conditions particulières. À ajouter dans le modèle (avec une migration),
   dans le serializer `ClaimSerializer` et dans le formulaire (`EMPTY_FORM`, `App.jsx` ligne 9) :
   - `type_sinistre` : `collision`, `sortie_de_route`, `vol`, `tentative_vol`, `bris_de_glace`, `incendie`,
     `climatique` ou `autre` (clés de `TYPES` dans `rag/policy_agent.py`) ;
   - `conditions_particulieres` (JSON), au format de `contrat_reference` dans
     `data/dossiers/dossiers_synthetiques.json` :
     ```json
     {"garanties": ["responsabilite_civile", "dommages_tous_accidents", "bris_de_glace", "vol", "assistance"],
      "conducteurs_designes": ["Sami Ben Salah"], "usage_declare": "privé et trajet travail",
      "date_souscription": "2025-03-01"}
     ```
     Noms de garanties reconnus : clés de `NOMS_GARANTIES` dans `rag/policy_agent.py`.

3. **Phrase générique de `decision_agent`.** Pour tout `insufficient_information`, `agents.py` (ligne 395) ajoute
   « Les Conditions particulières et les garanties souscrites doivent être vérifiées. », même quand elles ont été
   fournies et que la vraie raison est autre (couverture partielle, délai). Proposition : remplacer cette phrase par
   `policy_result.get("missing_information")`, que l'adaptateur ne remplit que lorsqu'elles manquent.

4. **Choix du contrat.** Le corpus RAG contient un contrat **fictif** rédigé par l'équipe (« Sérénité », 26 articles,
   `data/corpus/conditions_generales_auto.md`) et des extraits du Code des assurances. Le corpus de la version
   précédente est le contrat réel **AXA « Mon Auto »** (`backend/claims/corpus/axa_mon_auto_septembre_2026.pdf`,
   décrit par `backend/claims/policy_corpus.json`). Le bloc `rag` de `system_info`
   (`backend/claims/views.py`, lignes 31 à 50) décrit encore ce corpus et l'ancien moteur (embeddings Ollama,
   vecteurs en mémoire) : à mettre à jour selon le choix fait.

   Pour utiliser le contrat AXA :
   - convertir le PDF en Markdown au format attendu par `rag/chunking.py` : `# Chapitre …`, puis pour chaque article
     `## Article <id> — <titre>` (tiret cadratin), une ligne `source: contrat`, éventuellement `type: …`, puis le
     texte ;
   - **un seul contrat à la fois** : remplacer `conditions_generales_auto.md` plutôt que d'ajouter le fichier AXA. Les
     articles du contrat sont numérotés « 1 » à « 26 », et deux contrats dans l'index donneraient des identifiants en
     double et des garanties mélangées ;
   - adapter `GARANTIES_PAR_TYPE` et `NOMS_GARANTIES` dans `rag/policy_agent.py` aux garanties AXA ;
   - relancer l'indexation ([section 8](#8-indexation-du-corpus)) ;
   - l'évaluation (`rag/test_queries.json`, vérité terrain des dossiers) porte sur le contrat fictif. Elle ne vaut
     plus pour AXA tant qu'elle n'a pas été refaite.

   La version précédente forçait aussi `insufficient_information` pour un dossier tunisien face à un contrat
   français. L'agent RAG ne le fait pas : à reprendre si le contrat AXA France est retenu pour des dossiers tunisiens.

5. **Valeur `partial`.** Si `decision_agent` accepte un jour un statut `partial` (par exemple INVESTIGATE avec un
   motif dédié), changer la ligne `"partiel": "insufficient_information"` du dictionnaire `STATUTS` dans
   `rag/integration.py`, et les tests associés dans `rag/test_integration.py` (`test_statuts`,
   `test_partiel_en_investigation`).

---

## 10. Limites connues

- **Dossiers couverts sous conditions en ACCEPT automatique avec `qwen2.5:7b`.** Le modèle répond « couvert » dès
  qu'une garantie souscrite correspond, sans relever les conditions à vérifier. Exemples : D06 (vol : plainte et
  traces d'effraction, article 9) et D09 (vol déclaré au-delà de 2 jours ouvrés, article 17). Ces dossiers sortent en
  `covered`, puis en ACCEPT si aucun risque de fraude n'est détecté. Prévu en v3 : verdict déterminé par des règles,
  avec des vérifications déterministes (délais, pièces requises).
- **Instabilité du LLM sur les cas limites.** À température 0, deux lancements Gemini identiques ont donné des
  verdicts différents sur 3 dossiers sur 10 (D03, D08, D09). Les cas limites (seuil de « partiel », délai de
  déclaration) dépendent du modèle d'un appel à l'autre.
- **Petite évaluation.** 32 requêtes pour le retrieval, 10 dossiers pour l'agent complet : une requête vaut ~3 points
  de hit@k, un dossier vaut 10 % des verdicts. Les chiffres décrivent ce jeu de test, pas une performance générale.
- **Intakes simulés.** Dans l'évaluation, les faits du dossier sont des résumés rédigés à la main
  (`INTAKE_TEST` dans `rag/policy_agent.py`), pas la sortie réelle d'un agent d'extraction. Avec les champs bruts
  du formulaire (description libre, sans type ni tiers), les résultats n'ont pas été mesurés.
- **Anomalies entre pièces.** Photos qui contredisent le récit, facture gonflée, pièce manquante : le Policy Agent ne
  voit pas les pièces. C'est le rôle des agents Vision, Document et Fraud (D04 et D05 sortent en « couvert »).
