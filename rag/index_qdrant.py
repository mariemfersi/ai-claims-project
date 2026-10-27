"""Indexe les chunks « Par article » dans Qdrant avec le modèle dense retenu (bge-m3).

Usage :
    python rag/index_qdrant.py                              # Qdrant local, sans Docker (dossier qdrant_db/)
    python rag/index_qdrant.py --url http://localhost:6333  # serveur Qdrant
    QDRANT_URL=http://qdrant:6333 python rag/index_qdrant.py # idem ; retriever.py lit aussi QDRANT_URL

La collection est supprimée puis recréée à chaque lancement : relancer le script
donne toujours le même index. Vecteurs normalisés, distance cosinus. Le payload de
chaque point contient toutes les métadonnées du chunk, son id et son texte ; l'id
du point est la position du chunk dans chunk_corpus (même ordre que l'évaluation).
"""
import argparse, os, time
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from chunking import chunk_corpus, load_corpus, structure_chunks
from eval_retrieval import DEFAULT_MODEL

ROOT = Path(__file__).resolve().parent.parent
COLLECTION = "corpus_assurance"
LOCAL_PATH = ROOT / "qdrant_db"


def get_client(url=None):
    """Serveur Qdrant si url ou QDRANT_URL est défini (Docker), sinon mode local dans qdrant_db/."""
    url = url or os.environ.get("QDRANT_URL")
    return QdrantClient(url=url) if url else QdrantClient(path=str(LOCAL_PATH))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", help="URL d'un serveur Qdrant (par défaut : mode local dans qdrant_db/)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--corpus", default=str(ROOT / "data/corpus"))
    args = ap.parse_args()

    from sentence_transformers import SentenceTransformer
    chunks = chunk_corpus(load_corpus(args.corpus), structure_chunks)
    m = SentenceTransformer(args.model)
    prefix = "passage: " if "e5" in args.model else ""
    t0 = time.perf_counter()
    emb = m.encode([prefix + c["text"] for c in chunks], normalize_embeddings=True)
    print(f"{len(chunks)} chunks encodés avec {args.model} en {time.perf_counter() - t0:.0f} s")

    client = get_client(args.url)
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
    client.create_collection(COLLECTION, vectors_config=VectorParams(size=emb.shape[1], distance=Distance.COSINE))
    points = [PointStruct(id=i, vector=v.tolist(),
                          payload={**c["metadata"], "chunk_id": c["id"], "text": c["text"], "model": args.model})
              for i, (c, v) in enumerate(zip(chunks, emb))]
    for start in range(0, len(points), 128):
        client.upsert(COLLECTION, points[start:start + 128])
    print(f"Collection « {COLLECTION} » : {client.count(COLLECTION).count} points "
          f"({args.url or os.environ.get('QDRANT_URL') or LOCAL_PATH})")
    client.close()


if __name__ == "__main__":
    main()
