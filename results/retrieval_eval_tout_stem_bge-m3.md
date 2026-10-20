| Configuration | Chunks | hit@1 | hit@3 | hit@5 | MRR@5 | Tokens top-5 | Embeddings (s) |
|---|---|---|---|---|---|---|---|
| Taille fixe 500/50 + BM25 (stem) | 305 | 0.38 | 0.69 | 0.78 | 0.53 | 2491 | — |
| Taille fixe 500/50 + Dense (bge-m3) | 305 | 0.34 | 0.53 | 0.59 | 0.45 | 2491 | 282 |
| Taille fixe 500/50 + Hybride (RRF) | 305 | 0.44 | 0.78 | 0.88 | 0.61 | 2491 | 282 |
| Par article + BM25 (stem) | 594 | 0.56 | 0.81 | 0.81 | 0.68 | 1277 | — |
| Par article + Dense (bge-m3) | 594 | 0.62 | 0.81 | 0.84 | 0.71 | 1353 | 299 |
| Par article + Hybride (RRF) | 594 | 0.69 | 0.88 | 0.91 | 0.79 | 1297 | 299 |
