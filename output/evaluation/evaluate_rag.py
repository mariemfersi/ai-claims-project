"""Offline lexical retrieval diagnostic for page vs fixed-window chunking.

This evaluates the deterministic lexical fallback and, optionally, the configured
Ollama embedding model via --ollama.
"""
from collections import Counter
from pathlib import Path
import argparse
import json
import math
import re
import unicodedata
from urllib.request import Request, urlopen

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "backend" / "claims" / "corpus" / "axa_mon_auto_septembre_2026.pdf"
INDEX_FROM, INDEX_TO = 5, 103
K = 5

QUERIES = [
    ("Garantie dommages tous accidents dommages véhicule conditions garantie", {43, 71}),
    ("Le bris des feux arrière est-il couvert par le bris de glace ?", {40}),
    ("Franchise part indemnité reste charge sinistre", {49}),
    ("Déclarer sinistre délais formalités déclaration dommages véhicule", {53, 54}),
    ("Quelles garanties existent dans les différentes formules auto ?", {71}),
    ("Exclusions dommages conducteur état alcoolique stupéfiants", {43}),
    ("La garantie dommages tous accidents dépend-elle des conditions particulières ?", {43, 71}),
    ("Comment AXA indemnise les réparations du véhicule ?", {55, 56, 57}),
    ("Assistance dépannage en cas de panne et conditions pour appeler l’assisteur", {31}),
    ("Prise en charge des dommages causés aux tiers par la responsabilité civile", {55}),
    ("Montant de la franchise légale pour catastrophe naturelle véhicule", {47}),
    ("Dommages au véhicule après effraction et tentative de vol", {41}),
    ("Faut-il déclarer le sinistre avant toute réparation ou remplacement", {53}),
    ("Sanctions si l’assuré ne respecte pas les formalités et obligations de déclaration", {54}),
    ("Paiement direct au garage partenaire pour réparer le véhicule", {57}),
    ("Calcul de l’indemnisation si réparation chez un garage non partenaire", {56}),
]
STOP = {"quelle", "quelles", "quel", "quels", "est", "sont", "dans", "des", "les", "la", "le", "de", "du", "un", "une", "et", "en", "cas", "pour", "par", "à", "au", "aux", "l", "d", "il", "elle", "reste", "t", "assuré", "assuree"}


def norm(text):
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return [word for word in re.findall(r"[a-z0-9]+", text) if len(word) > 2 and word not in STOP]


def page_chunks(reader):
    return [{"page": n, "text": reader.pages[n - 1].extract_text() or ""} for n in range(INDEX_FROM, INDEX_TO + 1)]


def fixed_chunks(pages, size=500, overlap=50):
    result = []
    for page in pages:
        words = page["text"].split()
        start = 0
        while start < len(words):
            result.append({"page": page["page"], "text": " ".join(words[start:start + size])})
            if start + size >= len(words):
                break
            start += size - overlap
    return result


def rank(chunks, query):
    q = Counter(norm(query))
    scored = []
    for chunk in chunks:
        d = Counter(norm(chunk["text"]))
        score = sum(min(count, d.get(term, 0)) for term, count in q.items())
        if score:
            scored.append((score, chunk["page"]))
    return [page for _, page in sorted(scored, reverse=True)[:K]]


def evaluate(chunks):
    rr, hits = [], 0
    rows = []
    for query, gold in QUERIES:
        ranked_pages = rank(chunks, query)
        reciprocal = next((1 / i for i, page in enumerate(ranked_pages, 1) if page in gold), 0)
        hits += reciprocal > 0
        rr.append(reciprocal)
        rows.append((query, sorted(gold), ranked_pages, reciprocal))
    return {"hit_at_5": hits / len(QUERIES), "mrr_at_5": sum(rr) / len(rr), "rows": rows}


def ollama_embeddings(texts, model, batch_size=32):
    vectors = []
    for start in range(0, len(texts), batch_size):
        print(f"Embedding {start + 1}-{min(start + batch_size, len(texts))}/{len(texts)} avec {model}", flush=True)
        payload = json.dumps({"model": model, "input": texts[start:start + batch_size]}).encode()
        request = Request("http://localhost:11434/api/embed", data=payload, headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=600) as response:
            vectors.extend(json.loads(response.read())["embeddings"])
    return vectors


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0


def evaluate_embeddings(chunks, model):
    passage_vectors = ollama_embeddings([chunk["text"] for chunk in chunks], model)
    query_vectors = ollama_embeddings([query for query, _ in QUERIES], model)
    rr, hits, rows = [], 0, []
    for (query, gold), query_vector in zip(QUERIES, query_vectors):
        scored = sorted(((cosine(query_vector, vector), chunk["page"]) for vector, chunk in zip(passage_vectors, chunks)), reverse=True)
        ranked = [page for _, page in scored[:K]]
        reciprocal = next((1 / i for i, page in enumerate(ranked, 1) if page in gold), 0)
        hits += reciprocal > 0
        rr.append(reciprocal)
        rows.append((query, sorted(gold), ranked, reciprocal))
    return {"hit_at_5": hits / len(QUERIES), "mrr_at_5": sum(rr) / len(rr), "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ollama", action="store_true", help="also benchmark the configured Ollama embedding model")
    parser.add_argument("--model", default="nomic-embed-text:latest")
    args = parser.parse_args()
    pages = page_chunks(PdfReader(PDF))
    strategies = (("page", pages), ("fixed 500 words / overlap 50", fixed_chunks(pages)))
    for mode, evaluator in (("lexical", evaluate), *(([("ollama", lambda chunks: evaluate_embeddings(chunks, args.model))]) if args.ollama else [])):
        for label, chunks in strategies:
            result = evaluator(chunks)
            print(f"{mode} / {label}: chunks={len(chunks)} Hit@5={result['hit_at_5']:.3f} MRR@5={result['mrr_at_5']:.3f}")
            for query, gold, ranked, reciprocal in result["rows"]:
                print(f"  gold={gold} rank={ranked} RR={reciprocal:.3f} | {query}")
