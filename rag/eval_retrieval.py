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
from chunking import fixed_chunks, structure_chunks, chunk_corpus, load_corpus, n_tokens

ROOT = Path(__file__).resolve().parent.parent
K = 5


def tokenize(s):
    return re.findall(r"\w+", s.lower())


STOPWORDS = set("le la les de du des un une à au aux et ou en est que qui pour par "
                "sur dans avec ne pas se il elle d l".split())


def stem_tokenizer():
    """Tokenizer BM25 avec mots vides retirés et racinisation Snowball française."""
    import snowballstemmer
    stemmer = snowballstemmer.stemmer("french")
    return lambda s: stemmer.stemWords([t for t in tokenize(s) if t not in STOPWORDS])


class BM25:
    def __init__(self, chunks, stem=False):
        self.tok = stem_tokenizer() if stem else tokenize
        self.name = "BM25 (stem)" if stem else "BM25"
        self.bm = BM25Okapi([self.tok(c["text"]) for c in chunks])
    def rank(self, q):
        return list(np.argsort(-self.bm.get_scores(self.tok(q))))


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


class Hybrid:
    """Reciprocal Rank Fusion : score = 1/(k + rang_a) + 1/(k + rang_b), rangs à partir de 1."""
    name = "Hybride (RRF)"
    def __init__(self, a, b, k=60):
        self.a, self.b, self.k = a, b, k
    def rank(self, q):
        scores = {}
        for r in (self.a, self.b):
            for pos, idx in enumerate(r.rank(q), 1):
                scores[idx] = scores.get(idx, 0) + 1 / (self.k + pos)
        return sorted(scores, key=lambda i: -scores[i])


def evaluate(chunks, retriever, queries):
    hits = {1: 0, 3: 0, 5: 0}; rr = 0; ctx = []; detail = []
    for q in queries:
        full = retriever.rank(q["query"])
        order = full[:K]
        rank = next((i + 1 for i, idx in enumerate(order)
                     if set(chunks[idx]["metadata"]["articles"]) & set(q["expected"])), None)
        # rang dans le classement complet, pour l'analyse d'erreurs (n'entre pas dans les métriques)
        full_rank = rank or next((i + 1 for i, idx in enumerate(full)
                                  if set(chunks[idx]["metadata"]["articles"]) & set(q["expected"])), None)
        top = chunks[order[0]]["metadata"]
        for k in hits:
            hits[k] += bool(rank and rank <= k)
        rr += 1 / rank if rank else 0
        ctx.append(sum(n_tokens(chunks[i]["text"]) for i in order))
        detail.append({"id": q["id"], "rank": rank, "full_rank": full_rank,
                       "top1": top["articles"], "top1_titre": top.get("titre")})
    n = len(queries)
    return {"hit@1": hits[1] / n, "hit@3": hits[3] / n, "hit@5": hits[5] / n,
            "MRR@5": rr / n, "tokens_top5": float(np.mean(ctx)), "detail": detail}


def error_report(results, by_strategy, queries):
    """Analyse d'erreurs en Markdown : requêtes dont le bon article n'est pas 1er,
    puis tableau croisé BM25 / dense / hybride pour le chunking « Par article »."""
    qmap = {q["id"]: q for q in queries}
    lines = ["# Analyse d'erreurs du retrieval", "",
             "Requêtes dont aucun article attendu n'est dans le chunk classé 1er. "
             "Rang = position du premier bon chunk dans le classement complet.", ""]
    for key, r in results.items():
        miss = [d for d in r["detail"] if d["rank"] != 1]
        lines += [f"## {key}", "", f"{len(miss)} requête(s) sur {len(r['detail'])} pas en 1re position.", ""]
        if not miss:
            continue
        lines += ["| Requête | Texte | Attendus | Rang réel | Classé 1er à la place |", "|---|---|---|---|---|"]
        for d in miss:
            q = qmap[d["id"]]
            top = ", ".join(d["top1"]) or "(aucun article)"
            if d["top1_titre"]:
                top += f" — {d['top1_titre']}"
            lines.append(f"| {d['id']} | {q['query']} | {', '.join(q['expected'])} | "
                         f"{d['full_rank'] or 'absent'} | {top} |")
        lines.append("")

    per = by_strategy.get("Par article", {})
    if len(per) == 3:
        (bn, b), (dn, dd), (hn, h) = [(n, {d["id"] for d in r["detail"] if d["rank"] != 1})
                                      for n, r in per.items()]
        rows = [(f"{bn} seulement", b - dd - h), (f"{dn} seulement", dd - b - h),
                (f"{hn} seulement", h - b - dd), ("Les trois", b & dd & h)]
        lines += ["## Tableau croisé — Par article", "",
                  "Requêtes pas en 1re position, selon le ou les retrievers qui les ratent.", "",
                  "| Ratée par | Nb | Requêtes |", "|---|---|---|"]
        lines += [f"| {n} | {len(ids)} | {', '.join(sorted(ids)) or '—'} |" for n, ids in rows]
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="intfloat/multilingual-e5-small")
    ap.add_argument("--corpus", default=str(ROOT / "data/corpus"),
                    help="dossier contenant les .md du corpus (tous sont indexés)")
    ap.add_argument("--no-dense", action="store_true", help="BM25 seulement (rapide, sans modèle)")
    ap.add_argument("--rrf-k", type=int, default=60, help="constante k de la fusion RRF (hybride)")
    ap.add_argument("--filtre", choices=["tout", "direct"], default="tout",
                    help="direct : chunks du contrat ou lien_auto direct seulement (chunking « Par article » uniquement)")
    ap.add_argument("--bm25-stem", action="store_true",
                    help="BM25 (et donc l'hybride) avec racinisation française et mots vides retirés")
    args = ap.parse_args()
    # suffixe des fichiers de résultats, pour que les variantes ne s'écrasent pas
    suffix = args.filtre + ("_stem" if args.bm25_stem else "")

    corpus = load_corpus(args.corpus)
    print("Corpus :", ", ".join(corpus), f"— filtre : {args.filtre}")
    queries = json.loads((ROOT / "rag/test_queries.json").read_text(encoding="utf-8"))
    by_article = chunk_corpus(corpus, structure_chunks)
    if args.filtre == "direct":
        # la taille fixe n'a pas les métadonnées source / lien_auto : seul « Par article » est évalué
        by_article = [c for c in by_article if c["metadata"]["source"] == "contrat"
                      or c["metadata"]["lien_auto"] == "direct"]
        strategies = {"Par article": by_article}
    else:
        strategies = {"Taille fixe 500/50": chunk_corpus(corpus, fixed_chunks), "Par article": by_article}

    # requêtes dont tous les articles attendus sont exclus : gardées, elles comptent comme ratées
    kept = {a for c in by_article for a in c["metadata"]["articles"]}
    excluded = [q["id"] for q in queries if not set(q["expected"]) & kept]

    results = {}; by_strategy = {}
    for sname, chunks in strategies.items():
        retrievers = [BM25(chunks, stem=args.bm25_stem)]
        if not args.no_dense:
            # l'hybride réutilise les deux instances : embeddings calculés une seule fois
            retrievers += [Dense(chunks, args.model)]
            retrievers += [Hybrid(retrievers[0], retrievers[1], k=args.rrf_k)]
        for retr in retrievers:
            # « + » et non « | » : un « | » dans le nom casserait le tableau Markdown
            key = f"{sname} + {retr.name}"
            results[key] = evaluate(chunks, retr, queries)
            results[key]["n_chunks"] = len(chunks)
            by_strategy.setdefault(sname, {})[retr.name] = results[key]

    out = ROOT / "results"; out.mkdir(exist_ok=True)
    (out / f"retrieval_eval_{suffix}.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = ["| Configuration | Chunks | hit@1 | hit@3 | hit@5 | MRR@5 | Tokens top-5 |",
             "|---|---|---|---|---|---|---|"]
    for k, r in results.items():
        lines.append(f"| {k} | {r['n_chunks']} | {r['hit@1']:.2f} | {r['hit@3']:.2f} | "
                     f"{r['hit@5']:.2f} | {r['MRR@5']:.2f} | {r['tokens_top5']:.0f} |")
    table = "\n".join(lines)
    (out / f"retrieval_eval_{suffix}.md").write_text(table + "\n", encoding="utf-8")
    print(table)

    # requêtes ratées, pour l'analyse d'erreurs
    for k, r in results.items():
        miss = [d["id"] for d in r["detail"] if not d["rank"] or d["rank"] > 1]
        print(f"{k} — pas en 1re position : {', '.join(miss) or 'aucune'}")
    print(f"Requêtes dont tous les articles attendus sont exclus par le filtre : {', '.join(excluded) or 'aucune'}")

    report = error_report(results, by_strategy, queries)
    (out / f"erreurs_retrieval_{suffix}.md").write_text(report, encoding="utf-8")
    if "## Tableau croisé" in report:
        print("\n" + report[report.find("## Tableau croisé"):])


if __name__ == "__main__":
    main()
