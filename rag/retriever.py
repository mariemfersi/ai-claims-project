"""Recherche retenue : dense bge-m3 via Qdrant + BM25 racinisé en mémoire, fusion RRF.

Usage :
    from retriever import search
    for hit in search("Le bris de glace est-il couvert ?"):
        print(hit["rank"], hit["metadata"]["article"], hit["scores"]["rrf"])

    python rag/retriever.py "Le bris de glace est-il couvert ?"   # test en ligne de commande

Prérequis : avoir lancé rag/index_qdrant.py. Les chunks (texte et métadonnées) sont
relus depuis Qdrant, pour que BM25 et le dense travaillent sur le même ensemble.
Même calcul que « Par article + Hybride (RRF) » dans eval_retrieval.py --bm25-stem :
même tokenisation BM25, classements complets des deux retrievers, rangs à partir de 1,
score = 1/(k + rang_BM25) + 1/(k + rang_dense).

Le client Qdrant, le modèle et l'index BM25 sont chargés une seule fois, au premier appel.
En mode local, un seul processus peut ouvrir qdrant_db/ à la fois.
"""
import atexit, sys
from index_qdrant import COLLECTION, get_client
from eval_retrieval import BM25

RRF_K = 60
_state = {}


def _load(url=None):
    if _state:
        return _state
    from sentence_transformers import SentenceTransformer
    client = get_client(url)
    atexit.register(client.close)  # sinon le client local se ferme mal à l'arrêt de Python
    n = client.count(COLLECTION).count
    points, _ = client.scroll(COLLECTION, limit=n, with_payload=True, with_vectors=False)
    points.sort(key=lambda p: p.id)  # même ordre que chunk_corpus, donc que l'évaluation
    chunks = []
    for p in points:
        payload = dict(p.payload)
        text, chunk_id, model = payload.pop("text"), payload.pop("chunk_id"), payload.pop("model")
        chunks.append({"point_id": p.id, "id": chunk_id, "text": text, "metadata": payload})
    _state.update(client=client, chunks=chunks, model_name=model,
                  model=SentenceTransformer(model), bm25=BM25(chunks, stem=True))
    return _state


def search(query, k=5, url=None):
    """Renvoie les k meilleurs chunks : [{rank, id, text, metadata, scores}], où scores
    contient le score RRF, le rang et le score BM25, le rang et la similarité cosinus dense."""
    s = _load(url)
    chunks, n = s["chunks"], len(s["chunks"])
    prefix = "query: " if "e5" in s["model_name"] else ""
    qv = s["model"].encode([prefix + query], normalize_embeddings=True)[0]
    # classement dense complet, comme dans l'évaluation (594 points : coût négligeable)
    dense = s["client"].query_points(COLLECTION, query=qv.tolist(), limit=n).points
    dense_order = [p.id for p in dense]
    dense_score = {p.id: p.score for p in dense}
    bm25_scores = s["bm25"].bm.get_scores(s["bm25"].tok(query))
    bm25_order = [int(i) for i in s["bm25"].rank(query)]

    rrf, rank_of = {}, {"bm25": {}, "dense": {}}
    for name, order in (("bm25", bm25_order), ("dense", dense_order)):
        for pos, idx in enumerate(order, 1):
            rrf[idx] = rrf.get(idx, 0) + 1 / (RRF_K + pos)
            rank_of[name][idx] = pos
    top = sorted(rrf, key=lambda i: -rrf[i])[:k]
    return [{"rank": r, "id": chunks[i]["id"], "text": chunks[i]["text"], "metadata": chunks[i]["metadata"],
             "scores": {"rrf": rrf[i],
                        "bm25_rank": rank_of["bm25"][i], "bm25": float(bm25_scores[i]),
                        "dense_rank": rank_of["dense"][i], "dense": dense_score[i]}}
            for r, i in enumerate(top, 1)]


if __name__ == "__main__":
    for hit in search(" ".join(sys.argv[1:]) or "Le bris de glace est-il couvert ?"):
        m, sc = hit["metadata"], hit["scores"]
        print(f"{hit['rank']}. {m['article']} — {m['titre']}  (RRF {sc['rrf']:.4f} ; "
              f"BM25 rang {sc['bm25_rank']} ; dense rang {sc['dense_rank']}, cos {sc['dense']:.3f})")
