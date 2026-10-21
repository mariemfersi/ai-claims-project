"""Interface de démonstration du Policy Agent.

Usage :
    streamlit run demo/app.py

Toute la logique reste dans rag/ : l'interface appelle seulement retriever.search() et
policy_agent.analyse_couverture(), puis affiche leur résultat.

Mode démo (activé par défaut) : seules les réponses déjà présentes dans cache_llm/ sont
utilisées. Avant d'analyser, l'interface vérifie que la réponse P4 est en cache pour la
configuration choisie (modèle, reasoning_effort) ; sinon elle l'indique et n'analyse pas.
Par sécurité, la clé API est en plus retirée de l'environnement pendant l'analyse : même
en cas d'imprévu, aucun appel à Gemini ne peut partir. La clé n'est jamais demandée ni affichée.

Qdrant en mode local : un seul processus peut ouvrir qdrant_db/ ; ne pas lancer
d'évaluation pendant que l'interface tourne.
"""
import json, os, sys
from collections import Counter, defaultdict
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "rag"))

import policy_agent as pa  # noqa: E402
from chunking import chunk_corpus, load_corpus, structure_chunks  # noqa: E402
from eval_policy_agent import appels_prevus  # noqa: E402

EXEMPLES = ["Le bris de glace est-il couvert ?",
            "Je fais du VTC avec ma voiture personnelle, suis-je couvert ?",
            "Accident survenu au Maroc, suis-je assuré ?"]
COULEURS = {"couvert": "#1a7f37", "non_couvert": "#cf222e", "partiel": "#bc4c00", "indetermine": "#57606a"}
LIBELLES = {"couvert": "COUVERT", "non_couvert": "NON COUVERT", "partiel": "COUVERTURE PARTIELLE",
            "indetermine": "INDÉTERMINÉ"}
SOURCES = {"contrat": "Contrat", "code_assurances": "Code des assurances"}

st.set_page_config(page_title="Policy Agent — démo", layout="wide")


@st.cache_resource(show_spinner="Chargement du modèle bge-m3 et de l'index Qdrant…")
def charger_retriever():
    from retriever import search
    search("garantie")  # premier appel : charge le modèle, le client Qdrant et l'index BM25
    return search


@st.cache_resource
def textes_articles():
    """Texte complet de chaque article (toutes ses parties), pour les blocs dépliables."""
    textes = defaultdict(list)
    for c in chunk_corpus(load_corpus(ROOT / "data/corpus"), structure_chunks):
        textes[c["metadata"]["article"]].append(c["text"])
    return {a: "\n\n".join(t) for a, t in textes.items()}


@st.cache_data
def dossiers():
    return json.loads((ROOT / "data/dossiers/dossiers_synthetiques.json").read_text(encoding="utf-8"))


def configurations_en_cache():
    """(modèle, reasoning_effort) des réponses P4 présentes dans cache_llm/, avec leur nombre."""
    n = Counter()
    for f in pa.CACHE_DIR.glob("*.json"):
        c = json.loads(f.read_text(encoding="utf-8"))
        if c.get("etape") == "p4":
            n[(c["modele"], c.get("reasoning_effort") or "")] += 1
    return n


def badge_verdict(verdict, confiance):
    couleur = COULEURS.get(verdict, "#57606a")
    st.markdown(f"<div style='background:{couleur};color:#fff;padding:18px 24px;border-radius:10px;"
                f"font-size:2rem;font-weight:700;display:inline-block'>{LIBELLES.get(verdict, verdict)}</div>"
                f"<div style='margin-top:6px;color:gray'>confiance : {confiance}</div>", unsafe_allow_html=True)


def article_depliable(article, titre=None, source=None):
    textes = textes_articles()
    entete = f"Article {article}" + (f" — {titre}" if titre else "") + (f" ({SOURCES.get(source, source)})" if source else "")
    with st.expander(entete):
        st.text(textes.get(article, "Texte introuvable dans le corpus."))


# --- Barre latérale : configuration -------------------------------------------------------
with st.sidebar:
    st.header("Configuration")
    configs = {f"{m}|{e}": n for (m, e), n in configurations_en_cache().items()}  # « modèle|effort »
    # configuration de lancement, lue une seule fois : l'interface modifie ensuite os.environ
    actuelle = st.session_state.setdefault(
        "config_lancement",
        f"{os.environ.get('GEMINI_MODEL', pa.DEFAULT_MODEL)}|{os.environ.get('GEMINI_REASONING_EFFORT', 'low')}")
    options = list(dict.fromkeys([actuelle, *configs]))
    valeur = st.selectbox("Modèle et reasoning_effort", options,
                          index=options.index(max(configs, key=configs.get)) if configs else 0,
                          format_func=lambda o: f"{o.split('|')[0]} / {o.split('|')[1] or 'non envoyé'} "
                                                f"({configs.get(o, 0)} réponses P4 en cache)")
    choix = tuple(valeur.split("|"))
    os.environ["GEMINI_MODEL"], os.environ["GEMINI_REASONING_EFFORT"] = choix
    mode_demo = st.toggle("Mode démo (réponses en cache uniquement)", value=True)
    st.caption("Mode démo : aucun appel à l'API Gemini. Hors mode démo, chaque analyse non présente dans le "
               "cache consomme une requête du quota.")
    st.caption("Reformulation R1 : désactivée (réglage par défaut de l'agent).")

st.title("Policy Agent — analyse de couverture")
onglet_recherche, onglet_dossier = st.tabs(["Recherche", "Analyse d'un dossier"])

# --- Onglet 1 : recherche ----------------------------------------------------------------
with onglet_recherche:
    st.write("Recherche hybride (BM25 racinisé + bge-m3, fusion RRF) dans le contrat et le Code des assurances. "
             "Aucun appel à Gemini.")
    colonnes = st.columns(len(EXEMPLES))
    for col, exemple in zip(colonnes, EXEMPLES):
        if col.button(exemple, use_container_width=True):
            st.session_state["question"] = exemple
    question = st.text_input("Question", key="question", placeholder="Ex. : Quel est le délai pour déclarer un vol ?")
    if question:
        search = charger_retriever()
        for hit in search(question, k=5):
            m = hit["metadata"]
            st.markdown(f"**{hit['rank']}. Article {m['article']}** — {m['titre']}  \n"
                        f"<span style='color:gray'>{SOURCES.get(m['source'], m['source'])} · "
                        f"score RRF {hit['scores']['rrf']:.4f}</span>", unsafe_allow_html=True)
            with st.expander("Texte du passage"):
                st.text(hit["text"])

# --- Onglet 2 : analyse d'un dossier -------------------------------------------------------
with onglet_dossier:
    data = dossiers()
    ids = [d["id"] for d in data["dossiers"]]
    did = st.selectbox("Dossier", ids, format_func=lambda i: f"{i} — {next(d['scenario'] for d in data['dossiers'] if d['id'] == i)}")
    d = next(x for x in data["dossiers"] if x["id"] == did)
    declaration = d.get("declaration") or (d.get("audio") or {}).get("transcription_attendue")
    gauche, droite = st.columns(2)
    with gauche:
        st.subheader("Déclaration")
        st.write(declaration)
        if d.get("audio"):
            st.caption("Déclaration audio : transcription attendue.")
    with droite:
        st.subheader("Résultat attendu")
        st.write(f"Décision : **{d['attendu']['decision']}**")
        st.write(f"Articles : {', '.join(d['attendu']['articles'])}")
        if d["attendu"]["anomalies"]:
            st.write(f"Anomalies : {', '.join(d['attendu']['anomalies'])}")

    if st.button("Analyser", type="primary"):
        charger_retriever()
        intake = pa.intake_depuis_dossier(d, data["contrat_reference"])
        if mode_demo and appels_prevus([d], data["contrat_reference"], reformulation=False)[0] > 0:
            st.warning(f"Mode démo : la réponse de l'agent pour {did} n'est pas dans le cache avec la configuration "
                       f"{choix[0]} / {choix[1] or 'non envoyé'}. Choisissez une autre configuration, ou désactivez le "
                       "mode démo pour appeler l'API (une requête du quota).")
        else:
            cle = os.environ.pop("GEMINI_API_KEY", None) if mode_demo else None  # aucun appel possible en démo
            try:
                with st.spinner("Analyse en cours…"):
                    res = pa.analyse_couverture(intake)
            finally:
                if cle is not None:
                    os.environ["GEMINI_API_KEY"] = cle
            trace = res["trace"]
            origine = "réponse en cache" if all(a["statut"] == "cache" for a in trace["appels"]) else "appel à l'API"
            st.caption(f"{trace['modele']} / {trace['reasoning_effort'] or 'non envoyé'} — {origine}")
            badge_verdict(res["verdict_couverture"], res["confiance"])

            fournis = {a["article"]: a for a in trace["articles_fournis"]}
            st.subheader("Articles cités")
            if res["articles_cites"]:
                for a in res["articles_cites"]:
                    article_depliable(a, fournis.get(a, {}).get("titre"), fournis.get(a, {}).get("source"))
            else:
                st.write("Aucun article cité.")
            st.subheader("Justification")
            st.write(res["justification"])
            if res["exclusions_applicables"]:
                st.write("Exclusions : " + " ; ".join(f"article {e['article']} : {e['motif']}"
                                                       for e in res["exclusions_applicables"]))
            if res["franchise"]:
                f = res["franchise"]
                st.write(f"Franchise : {f.get('montant') or 'non chiffrée'}"
                         + (f" (article {f['article']})" if f.get("article") else "") + f" — {f.get('detail', '')}")
            if trace["avertissements"]:
                for a in trace["avertissements"]:
                    st.info(a)
            with st.expander("Détail : sous-questions et articles fournis"):
                st.markdown("**Sous-questions**")
                for q in trace["sous_questions"]:
                    st.write(f"{q['id']}. [{q['theme']}] {q['originale']}"
                             + (f"  \n→ *{q['reformulee']}*" if q.get("reformulee") else ""))
                st.markdown(f"**Articles fournis au modèle ({len(trace['articles_fournis'])})**")
                st.table([{"article": a["article"], "titre": a["titre"], "source": SOURCES.get(a["source"], a["source"]),
                           "sélection": a.get("selection", ""), "questions": ", ".join(map(str, a["questions"]))}
                          for a in trace["articles_fournis"]])
