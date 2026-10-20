"""Deux stratégies de chunking pour le corpus (contrat + Code des assurances).

- fixed_chunks     : baseline, fenêtre de 500 tokens avec overlap de 50
- structure_chunks : un chunk par article, avec métadonnées (chapitre, n° d'article, type, source)

Chaque chunk est un dict : {id, text, metadata}. metadata["articles"] liste les
identifiants d'articles présents dans le chunk (sert à l'évaluation hit@k / MRR).

Identifiants : les articles du contrat sont numérotés "1" à "26", ceux du Code des
assurances gardent leur numéro officiel ("L113-2", "R211-10", "A121-1-annexe-4") :
il n'y a donc pas de collision entre les deux documents.

Format attendu de chaque fichier Markdown :
    # Chapitre ...
    ## Article <id> — <titre>
    type: <type>              (optionnel)
    source: <source>          (optionnel, "contrat" par défaut)
    lien_auto: direct|indirect (optionnel, Code des assurances)
    <texte>

Articles longs : un modèle d'embeddings ne lit qu'un nombre limité de tokens
(512 pour multilingual-e5-small) et ignore la suite. Un article plus long que
`max_tokens` est donc découpé en plusieurs chunks, à la frontière des alinéas ;
chaque partie garde le chapitre et le titre de l'article, et le même identifiant
d'article dans ses métadonnées.
"""
import re
from pathlib import Path
import tiktoken

ENC = tiktoken.get_encoding("cl100k_base")
ARTICLE_RE = re.compile(r"^## Article (\S+) — (.+)$", re.M)
CHAPTER_RE = re.compile(r"^# (Chapitre .+)$", re.M)
META_RE = re.compile(r"^(type|source|lien_auto): (\S+)\n", re.M)


def load_corpus(corpus_dir):
    """Renvoie {nom_fichier: texte} pour tous les .md du dossier, dans l'ordre alphabétique."""
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(Path(corpus_dir).glob("*.md"))}


def _article_spans(text):
    """Renvoie [(id, start, end)] pour chaque article du texte."""
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


def _split_long(lines, max_tokens):
    """Regroupe des alinéas en paquets de max_tokens au plus (un alinéa trop long est coupé par phrases)."""
    units = []
    for l in lines:
        if n_tokens(l) <= max_tokens:
            units.append(l)
        else:
            units.extend(x for x in re.split(r"(?<=[.;:])\s+", l) if x)
    parts, cur = [], []
    for u in units:
        if cur and n_tokens("\n".join(cur + [u])) > max_tokens:
            parts.append(cur); cur = []
        cur.append(u)
    if cur:
        parts.append(cur)
    return parts


def structure_chunks(text, source_file="", max_tokens=450):
    chunks = []
    chapter = None
    chapter_pos = [(m.start(), m.group(1)) for m in CHAPTER_RE.finditer(text)]
    for num, start, end in _article_spans(text):
        for pos, name in chapter_pos:
            if pos < start:
                chapter = name
        body = text[start:end].strip()
        title = ARTICLE_RE.match(body).group(2)
        meta = dict(META_RE.findall(body))
        clean = META_RE.sub("", body)
        metadata = {"article": num, "titre": title, "chapitre": chapter,
                    "type_garantie": meta.get("type", "general"),
                    "source": meta.get("source", "contrat"),
                    "lien_auto": meta.get("lien_auto"),
                    "fichier": source_file, "articles": [num]}
        # le titre du chapitre est préfixé pour donner du contexte à l'embedding
        full = f"{chapter}\n{clean}"
        if n_tokens(full) <= max_tokens:
            chunks.append({"id": f"art-{num}", "text": full, "metadata": metadata})
            continue
        head, *lines = clean.split("\n")
        budget = max_tokens - n_tokens(f"{chapter}\n{head} (partie 99/99)\n")
        parts = _split_long(lines, max(budget, 100))
        for k, part in enumerate(parts, 1):
            chunks.append({"id": f"art-{num}-p{k}",
                           "text": f"{chapter}\n{head} (partie {k}/{len(parts)})\n" + "\n".join(part),
                           "metadata": {**metadata, "partie": k, "nb_parties": len(parts)}})
    return chunks


def fixed_chunks(text, size=500, overlap=50, source_file=""):
    tokens = ENC.encode(text)
    spans = _article_spans(text)
    # position caractère -> article, pour savoir quels articles chaque fenêtre recouvre
    chunks, start, i = [], 0, 0
    while start < len(tokens):
        window = tokens[start:start + size]
        char_start = len(ENC.decode(tokens[:start]))
        char_end = char_start + len(ENC.decode(window))
        arts = [n for n, s, e in spans if s < char_end and e > char_start]
        chunks.append({"id": f"fix-{Path(source_file).stem}-{i}", "text": ENC.decode(window),
                       "metadata": {"articles": arts, "fichier": source_file}})
        if start + size >= len(tokens):
            break
        start += size - overlap
        i += 1
    return chunks


def chunk_corpus(corpus, strategy):
    """Applique une stratégie à chaque fichier séparément (une fenêtre ne chevauche
    jamais deux documents) et concatène les chunks."""
    out = []
    for name, text in corpus.items():
        out.extend(strategy(text, source_file=name))
    return out


def n_tokens(s):
    return len(ENC.encode(s))
