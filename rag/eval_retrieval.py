"""Évaluation du retrieval : 2 stratégies de chunking x 2 retrievers (BM25, dense).

Usage :
    python rag/eval_retrieval.py                      # e5-small (rapide, CPU)
    python rag/eval_retrieval.py --model BAAI/bge-m3  # modèle cible du projet (plus lourd)

Métriques : hit@1, hit@3, hit@5, MRR@5, et nombre moyen de tokens envoyés au LLM
pour le top-5 (coût / bruit du contexte).
"""
import argparse, json, re
from pathlib import Path
import numpy as np
from rank_bm25 import BM25Okapi
from chunking import fixed_chunks, structure_chunks, n_tokens

ROOT = Path(__file__).resolve().parent.parent
K = 5


def tokenize(s):
    return re.findall(r"\w+", s.lower())


class BM25:
    name = "BM25"
    def __init__(self, chunks):
        self.bm = BM25Okapi([tokenize(c["text"]) for c in chunks])
    def rank(self, q):
        return list(np.argsort(-self.bm.get_scores(tokenize(q))))


class Dense:
    def __init__(self, chunks, model):
        from sentence_transformers import SentenceTransformer
        self.name = f"Dense ({model.split('/')[-1]})"
        self.m = SentenceTransformer(model)
        self.e5 = "e5" in model
        p = [("passage: " if self.e5 else "") + c["text"] for c in chunks]
        self.emb = self.m.encode(p, normalize_embeddings=True)
    def rank(self, q):
        qe = self.m.encode([("query: " if self.e5 else "") + q], normalize_embeddings=True)[0]
        return list(np.argsort(-(self.emb @ qe)))


def evaluate(chunks, retriever, queries):
    hits = {1: 0, 3: 0, 5: 0}; rr = 0; ctx = []; detail = []
    for q in queries:
        order = retriever.rank(q["query"])[:K]
        rank = next((i + 1 for i, idx in enumerate(order)
                     if set(chunks[idx]["metadata"]["articles"]) & set(q["expected"])), None)
        for k in hits:
            hits[k] += bool(rank and rank <= k)
        rr += 1 / rank if rank else 0
        ctx.append(sum(n_tokens(chunks[i]["text"]) for i in order))
        detail.append({"id": q["id"], "rank": rank,
                       "top1": chunks[order[0]]["metadata"]["articles"]})
    n = len(queries)
    return {"hit@1": hits[1] / n, "hit@3": hits[3] / n, "hit@5": hits[5] / n,
            "MRR@5": rr / n, "tokens_top5": float(np.mean(ctx)), "detail": detail}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="intfloat/multilingual-e5-small")
    args = ap.parse_args()

    text = (ROOT / "data/corpus/conditions_generales_auto.md").read_text(encoding="utf-8")
    queries = json.loads((ROOT / "rag/test_queries.json").read_text(encoding="utf-8"))
    strategies = {"Taille fixe 500/50": fixed_chunks(text), "Par article": structure_chunks(text)}

    results = {}
    for sname, chunks in strategies.items():
        for retr in (BM25(chunks), Dense(chunks, args.model)):
            key = f"{sname} | {retr.name}"
            results[key] = evaluate(chunks, retr, queries)
            results[key]["n_chunks"] = len(chunks)

    out = ROOT / "results"; out.mkdir(exist_ok=True)
    (out / "retrieval_eval.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = ["| Configuration | Chunks | hit@1 | hit@3 | hit@5 | MRR@5 | Tokens top-5 |",
             "|---|---|---|---|---|---|---|"]
    for k, r in results.items():
        lines.append(f"| {k} | {r['n_chunks']} | {r['hit@1']:.2f} | {r['hit@3']:.2f} | "
                     f"{r['hit@5']:.2f} | {r['MRR@5']:.2f} | {r['tokens_top5']:.0f} |")
    table = "\n".join(lines)
    (out / "retrieval_eval.md").write_text(table + "\n", encoding="utf-8")
    print(table)

    # requêtes ratées, pour l'analyse d'erreurs
    for k, r in results.items():
        miss = [d["id"] for d in r["detail"] if not d["rank"] or d["rank"] > 1]
        print(f"{k} — pas en 1re position : {', '.join(miss) or 'aucune'}")


if __name__ == "__main__":
    main()
