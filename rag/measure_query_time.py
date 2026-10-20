"""Temps d'encodage d'une requête par le modèle dense (latence côté retrieval).

Usage :
    python rag/measure_query_time.py --model BAAI/bge-m3
    python rag/measure_query_time.py --model intfloat/multilingual-e5-small

Un premier appel d'échauffement, puis les requêtes de test encodées une par une
(préfixe "query: " pour e5) ; affiche les temps moyen, médian et maximal.
"""
import argparse, json, statistics, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="BAAI/bge-m3")
    args = ap.parse_args()

    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(args.model)
    prefix = "query: " if "e5" in args.model else ""
    queries = [q["query"] for q in json.loads((ROOT / "rag/test_queries.json").read_text(encoding="utf-8"))]

    m.encode([prefix + "échauffement"], normalize_embeddings=True)
    times = []
    for q in queries:
        t0 = time.perf_counter()
        m.encode([prefix + q], normalize_embeddings=True)
        times.append(time.perf_counter() - t0)
    print(f"{args.model} : {len(times)} requêtes — moyenne {1000 * statistics.mean(times):.1f} ms, "
          f"médiane {1000 * statistics.median(times):.1f} ms, max {1000 * max(times):.1f} ms")


if __name__ == "__main__":
    main()
