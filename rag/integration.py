"""Adaptateur du Policy Agent au format du backend Django (branche ines), sans dépendance à Django.

Usage côté backend :
    from rag.integration import policy_agent_pour_backend
    resultat = policy_agent_pour_backend({"incident_date": claim.incident_date, "location": claim.location,
                                          "description": claim.description, "policy_number": claim.policy_number,
                                          "customer_name": claim.customer_name})

Entrée : les champs du modèle Claim (incident_date, location, description, policy_number,
customer_name) et, en option, conditions_particulieres, type_sinistre, tiers_implique, conducteur.
Sortie : les clés de policy_agent(claim) de backend/claims/agents.py (agent, engine, model,
embedding_model, coverage_status, references, retrieved_chunks, retrieval_query, explanation,
missing_information, confidence, diagnostic_error), plus verdict_couverture, articles_cites,
franchise et trace.

references : {page, section, source, text, article}, les clés lues par frontend/src/App.jsx.
Le corpus est découpé par article, pas par page : page vaut None (le frontend affiche « Page ? ») ;
section porte « Article 15 — titre » et source « Contrat » ou « Code des assurances ».

Une erreur (Gemini, Qdrant, import) ne lève pas d'exception : coverage_status vaut
insufficient_information, explanation dit ce qui s'est passé et diagnostic_error le type d'erreur.
"""
import os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # policy_agent importe chunking, retriever…

STATUTS = {"couvert": "covered", "partiel": "covered", "non_couvert": "excluded",
           "indetermine": "insufficient_information"}
CONFIANCE_NUM = {"haute": 0.9, "moyenne": 0.6, "basse": 0.3}
SOURCES = {"contrat": "Contrat", "code_assurances": "Code des assurances"}
CP_MANQUANTES = "Conditions particulières et garanties souscrites"
LONGUEUR_EXTRAIT = 600

# Type de sinistre déduit de la description quand le backend ne le fournit pas (le modèle Claim
# n'a pas ce champ). Premier mot-clé trouvé, dans cet ordre ; sinon None.
MOTS_TYPE = [("tentative_vol", ("tentative de vol",)),
             ("vol", ("vol ", "volé", "volée", "dérobé")),
             ("bris_de_glace", ("pare-brise", "vitre", "lunette arrière", "bris de glace")),
             ("incendie", ("incendie", "brûlé", "pris feu")),
             ("climatique", ("grêle", "tempête", "inondation")),
             ("collision", ("percuté", "heurté par", "collision", "accroché", "accident avec")),
             ("sortie_de_route", ("sortie de route", "fossé", "perdu le contrôle"))]


def type_sinistre(description):
    texte = f" {(description or '').lower()} "
    return next((t for t, mots in MOTS_TYPE if any(m in texte for m in mots)), None)


def intake_depuis_claim(claim):
    """Intake au format de analyse_couverture (schéma P1) à partir des champs du modèle Claim."""
    date = claim.get("incident_date")
    return {"date_sinistre": date.isoformat() if hasattr(date, "isoformat") else date,
            "heure": None, "lieu": claim.get("location"),
            "type_sinistre": claim.get("type_sinistre") or type_sinistre(claim.get("description")),
            "tiers_implique": claim.get("tiers_implique"),
            "conducteur": claim.get("conducteur") or claim.get("customer_name"),
            "souscripteur": claim.get("customer_name"),
            "circonstances": claim.get("description"), "zone_impact_declaree": None,
            "usage_au_moment_du_sinistre": claim.get("usage_au_moment_du_sinistre"),
            "ecarts_formulaire": [], "remarques": [],
            "conditions_particulieres": claim.get("conditions_particulieres")}


def _textes_articles():
    """Texte de chaque article (toutes ses parties), relu dans les chunks déjà chargés par le
    retriever : pas de nouvelle recherche. Vide si le retriever n'a pas été chargé."""
    try:
        from retriever import _state
    except Exception:
        return {}
    parties = {}
    for c in _state.get("chunks", []):
        m = c["metadata"]
        if "article" in m:
            parties.setdefault(m["article"], []).append((m.get("partie", 1), c["text"]))
    return {a: "\n".join(t for _, t in sorted(p)) for a, p in parties.items()}


def _reference(article, textes):
    texte = textes.get(article["article"], "")
    if len(texte) > LONGUEUR_EXTRAIT:
        texte = texte[:LONGUEUR_EXTRAIT].rstrip() + "…"
    return {"page": None, "section": f"Article {article['article']} — {article.get('titre', '')}".rstrip(" —"),
            "source": SOURCES.get(article.get("source"), article.get("source")), "text": texte,
            "article": article["article"]}


def _modele_embeddings():
    try:
        from retriever import _state
        return _state.get("model_name")
    except Exception:
        return None


def policy_agent_pour_backend(claim: dict, cache=True) -> dict:
    intake = intake_depuis_claim(claim)
    manquantes = [] if intake["conditions_particulieres"] else [CP_MANQUANTES]
    diagnostic = None
    try:
        from policy_agent import analyse_couverture
        rep = analyse_couverture(intake, cache=cache)
    except Exception as e:  # Qdrant indisponible, dépendance manquante… : jamais d'exception vers Django
        diagnostic = type(e).__name__
        rep = {"verdict_couverture": "indetermine", "articles_cites": [], "franchise": None, "confiance": "basse",
               "justification": f"Analyse de couverture impossible ({type(e).__name__} : {e}). "
                                "La couverture doit être vérifiée manuellement.",
               "trace": {"erreur": repr(e)}}
    trace = rep.get("trace") or {}
    if diagnostic is None and rep["justification"].startswith("Analyse impossible"):
        diagnostic = "GeminiError"  # échec d'appel rattrapé par analyse_couverture (indetermine)

    fournis = trace.get("articles_fournis") or []
    textes = _textes_articles()
    cites = set(rep.get("articles_cites") or [])
    refs = [a for a in fournis if a["article"] in cites] or fournis[:3]
    if rep["verdict_couverture"] == "indetermine" and diagnostic is not None:
        refs = []
    explication = rep["justification"]
    if rep["verdict_couverture"] == "partiel":
        explication = f"Couverture partielle. {explication}"
    return {"agent": "policy_rag", "engine": "gemini-rag" if diagnostic is None else "gemini-rag-erreur",
            "model": trace.get("modele") or os.environ.get("GEMINI_MODEL"),
            "embedding_model": _modele_embeddings(),
            "coverage_status": STATUTS.get(rep["verdict_couverture"], "insufficient_information"),
            "references": [_reference(a, textes) for a in refs],
            "retrieved_chunks": [{**_reference(a, textes), "similarity": round(a.get("score", 0.0), 4)}
                                 for a in fournis],
            "retrieval_query": "\n".join(q["originale"] for q in trace.get("sous_questions", [])),
            "explanation": explication, "missing_information": manquantes,
            "confidence": CONFIANCE_NUM.get(rep.get("confiance"), 0.3),
            "diagnostic_error": diagnostic,
            "verdict_couverture": rep["verdict_couverture"], "articles_cites": rep.get("articles_cites") or [],
            "franchise": rep.get("franchise"), "trace": trace}
