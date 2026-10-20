"""Test de parité : retriever.search() doit reproduire l'évaluation retenue.

Usage :
    python rag/index_qdrant.py            # si l'index n'existe pas encore
    python rag/test_retriever_parity.py

Compare, pour les 32 requêtes de test, le rang du premier bon chunk (classement
complet) et l'article classé 1er avec « Par article + Hybride (RRF) » dans
results/retrieval_eval_tout_stem_bge-m3.json. Code de sortie 1 au premier écart
constaté (toutes les requêtes sont quand même vérifiées et les écarts affichés).
"""
import json, sys
from pathlib import Path
from retriever import search

ROOT = Path(__file__).resolve().parent.parent
REFERENCE = ROOT / "results/retrieval_eval_tout_stem_bge-m3.json"
CONFIG = "Par article + Hybride (RRF)"


def main():
    ref = json.loads(REFERENCE.read_text(encoding="utf-8"))[CONFIG]["detail"]
    ref = {d["id"]: d for d in ref}
    queries = json.loads((ROOT / "rag/test_queries.json").read_text(encoding="utf-8"))
    diffs = []
    for q in queries:
        hits = search(q["query"], k=10_000)  # classement complet, pour comparer full_rank
        full_rank = next((h["rank"] for h in hits if set(h["metadata"]["articles"]) & set(q["expected"])), None)
        top1 = hits[0]["metadata"]["articles"]
        r = ref[q["id"]]
        if full_rank != r["full_rank"] or top1 != r["top1"]:
            diffs.append(q["id"])
            print(f"ÉCART {q['id']} : rang {full_rank} (évaluation {r['full_rank']}), "
                  f"1er {top1} (évaluation {r['top1']})")
    print(f"{len(queries) - len(diffs)}/{len(queries)} requêtes identiques à {REFERENCE.name}")
    sys.exit(1 if diffs else 0)


if __name__ == "__main__":
    main()
