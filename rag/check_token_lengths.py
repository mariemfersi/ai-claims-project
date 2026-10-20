"""Vérifie que les chunks tiennent dans la fenêtre du modèle dense (pas de troncature).

Usage :
    python rag/check_token_lengths.py --model intfloat/multilingual-e5-small
    python rag/check_token_lengths.py --model BAAI/bge-m3

Pour chaque chunking (taille fixe, par article), compte les chunks dont la longueur,
mesurée avec le tokenizer du modèle (tokens spéciaux compris, préfixe "passage: " pour
e5), dépasse la limite à laquelle SentenceTransformer tronque (max_seq_length), et
affiche les 10 plus longs.
"""
import argparse
from pathlib import Path
from chunking import fixed_chunks, structure_chunks, chunk_corpus, load_corpus

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="BAAI/bge-m3")
    ap.add_argument("--corpus", default=str(ROOT / "data/corpus"))
    ap.add_argument("--top", type=int, default=10, help="nombre de chunks les plus longs à afficher")
    args = ap.parse_args()

    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(args.model)
    limit = m.max_seq_length
    prefix = "passage: " if "e5" in args.model else ""
    corpus = load_corpus(args.corpus)
    print(f"Modèle : {args.model} — limite : {limit} tokens — préfixe : {prefix!r}")

    for sname, strategy in {"Taille fixe 500/50": fixed_chunks, "Par article": structure_chunks}.items():
        chunks = chunk_corpus(corpus, strategy)
        lengths = sorted(((len(m.tokenizer(prefix + c["text"])["input_ids"]), c["id"]) for c in chunks),
                         reverse=True)
        over = sum(n > limit for n, _ in lengths)
        print(f"\n## {sname} : {len(chunks)} chunks, {over} au-dessus de {limit}, "
              f"plus long : {lengths[0][0]}")
        for n, cid in lengths[:args.top]:
            print(f"{n:6d}  {cid}")


if __name__ == "__main__":
    main()
