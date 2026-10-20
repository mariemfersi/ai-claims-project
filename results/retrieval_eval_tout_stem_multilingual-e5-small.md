| Configuration | Chunks | hit@1 | hit@3 | hit@5 | MRR@5 | Tokens top-5 | Embeddings (s) |
|---|---|---|---|---|---|---|---|
| Taille fixe 500/50 + BM25 (stem) | 305 | 0.38 | 0.69 | 0.78 | 0.53 | 2491 | — |
| Taille fixe 500/50 + Dense (multilingual-e5-small) | 305 | 0.31 | 0.53 | 0.56 | 0.41 | 2491 | 28 |
| Taille fixe 500/50 + Hybride (RRF) | 305 | 0.56 | 0.69 | 0.81 | 0.65 | 2491 | 28 |
| Par article + BM25 (stem) | 594 | 0.56 | 0.81 | 0.81 | 0.68 | 1277 | — |
| Par article + Dense (multilingual-e5-small) | 594 | 0.59 | 0.75 | 0.78 | 0.67 | 1140 | 25 |
| Par article + Hybride (RRF) | 594 | 0.62 | 0.78 | 0.81 | 0.71 | 1286 | 25 |
