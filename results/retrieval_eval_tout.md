| Configuration | Chunks | hit@1 | hit@3 | hit@5 | MRR@5 | Tokens top-5 |
|---|---|---|---|---|---|---|
| Taille fixe 500/50 + BM25 | 305 | 0.41 | 0.62 | 0.72 | 0.51 | 2491 |
| Taille fixe 500/50 + Dense (multilingual-e5-small) | 305 | 0.31 | 0.53 | 0.56 | 0.41 | 2491 |
| Taille fixe 500/50 + Hybride (RRF) | 305 | 0.50 | 0.66 | 0.72 | 0.59 | 2491 |
| Par article + BM25 | 594 | 0.56 | 0.78 | 0.81 | 0.67 | 1360 |
| Par article + Dense (multilingual-e5-small) | 594 | 0.59 | 0.75 | 0.78 | 0.67 | 1140 |
| Par article + Hybride (RRF) | 594 | 0.59 | 0.78 | 0.78 | 0.68 | 1341 |
