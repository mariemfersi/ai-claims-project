"""Deux stratégies de chunking pour le corpus des conditions générales.

- fixed_chunks     : baseline, fenêtre de 500 tokens avec overlap de 50
- structure_chunks : un chunk par article, avec métadonnées (chapitre, n° d'article, type de garantie)

Chaque chunk est un dict : {id, text, metadata}. metadata["articles"] liste les
numéros d'articles présents dans le chunk (sert à l'évaluation hit@k / MRR).
"""
import re
import tiktoken

ENC = tiktoken.get_encoding("cl100k_base")
ARTICLE_RE = re.compile(r"^## Article (\d+) — (.+)$", re.M)
CHAPTER_RE = re.compile(r"^# (Chapitre .+)$", re.M)


def _article_spans(text):
    """Renvoie [(num, start, end)] pour chaque article du corpus."""
    matches = list(ARTICLE_RE.finditer(text))
    spans = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        # coupe aussi au prochain titre de chapitre
        nxt = CHAPTER_RE.search(text, m.end(), end)
        if nxt:
            end = nxt.start()
        spans.append((m.group(1), m.start(), end))
    return spans


def structure_chunks(text):
    chunks = []
    chapter = None
    chapter_pos = [(m.start(), m.group(1)) for m in CHAPTER_RE.finditer(text)]
    for num, start, end in _article_spans(text):
        for pos, name in chapter_pos:
            if pos < start:
                chapter = name
        body = text[start:end].strip()
        title = ARTICLE_RE.match(body).group(2)
        type_m = re.search(r"^type: (\w+)$", body, re.M)
        gtype = type_m.group(1) if type_m else "general"
        clean = re.sub(r"^type: \w+\n", "", body, flags=re.M)
        chunks.append({
            "id": f"art-{num}",
            # le titre du chapitre est préfixé pour donner du contexte à l'embedding
            "text": f"{chapter}\n{clean}",
            "metadata": {"article": num, "titre": title, "chapitre": chapter,
                         "type_garantie": gtype, "articles": [num]},
        })
    return chunks


def fixed_chunks(text, size=500, overlap=50):
    tokens = ENC.encode(text)
    spans = _article_spans(text)
    # position caractère -> article, pour savoir quels articles chaque fenêtre recouvre
    chunks, start, i = [], 0, 0
    while start < len(tokens):
        window = tokens[start:start + size]
        char_start = len(ENC.decode(tokens[:start]))
        char_end = char_start + len(ENC.decode(window))
        arts = [n for n, s, e in spans if s < char_end and e > char_start]
        chunks.append({"id": f"fix-{i}", "text": ENC.decode(window),
                       "metadata": {"articles": arts}})
        if start + size >= len(tokens):
            break
        start += size - overlap
        i += 1
    return chunks


def n_tokens(s):
    return len(ENC.encode(s))
