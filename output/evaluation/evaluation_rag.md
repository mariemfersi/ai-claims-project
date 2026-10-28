# Évaluation courte du retrieval RAG

**Date :** 28 octobre 2026 · **Corpus :** Conditions générales AXA France « Mon Auto », septembre 2026, pages 5–103.
**Reproductibilité :** `python output/evaluation/evaluate_rag.py --ollama --model nomic-embed-text:latest` (pypdf requis et Ollama lancé).

## Protocole

Huit requêtes couvrent les garanties dommages, le bris de glace, la franchise, les formalités de déclaration, les formules, les exclusions et l’indemnisation. Les pages pertinentes sont annotées manuellement à partir du PDF. On compare deux segmentations : une page par passage (99 passages) et une fenêtre fixe de 500 mots avec chevauchement de 50 mots (131 passages). Le score lexical dénombre les termes de requête présents dans chaque passage ; les cinq passages les mieux classés sont retenus.

Deux classements ont été mesurés. Le baseline lexical compte les termes de requête présents dans le passage. Le benchmark sémantique appelle le vrai modèle Ollama `nomic-embed-text:latest` (chargé sur GPU, contexte annoncé 2048) puis trie les vecteurs par similarité cosinus. Il teste les mêmes requêtes, passages et pages de référence que le baseline.

## Résultats

| Retriever | Segmentation | Passages | Hit@5 | MRR@5 |
|---|---|---:|---:|---:|
| Lexical | Page entière | 99 | 1,000 | 0,754 |
| Lexical | 500 mots / overlap 50 | 131 | 1,000 | 0,760 |
| Nomic embeddings + cosinus | Page entière | 99 | 1,000 | 0,583 |
| Nomic embeddings + cosinus | 500 mots / overlap 50 | 131 | 1,000 | 0,646 |

Avec les embeddings, les fenêtres fixes améliorent le MRR de 0,063 sur ce jeu ; le Hit@5 reste identique. Ce résultat soutient un essai plus large des fenêtres, mais huit questions ne suffisent pas pour modifier la segmentation de production à elles seules. Les pages conservent une référence directe au contrat. Le baseline lexical produit un écart de MRR de seulement 0,006 entre les stratégies. Les rangs détaillés du benchmark sémantique apparaissent ci-dessous.

## Questions, pages de référence et rangs observés

| Question | Pages pertinentes | Rang lexical, pages | Rang lexical, fenêtres |
|---|---|---|---|
| Garantie dommages tous accidents et dommages véhicule | 43, 71 | 1, 4 | 1, 5 |
| Bris des feux arrière et bris de glace | 40 | 1 | 1 |
| Part de l’indemnité à la charge après sinistre (franchise) | 49 | 5 | 4 |
| Délais et formalités pour déclarer un sinistre | 53, 54 | 1, absent | 1, absent |
| Garanties selon les formules auto | 71 | 2 | 2 |
| Exclusions en cas d’état alcoolique | 43 | 1 | 1 |
| Garantie dommages tous accidents mentionnée aux Conditions particulières | 43, 71 | 3, absent | 3, absent |
| Modalités d’indemnisation des réparations | 55, 56, 57 | absent, 1, 2 | absent, 1, 2 |

### Rang des pages pertinentes avec les embeddings Nomic

| Question | Pages pertinentes | Top 5 pages, segmentation par page | Top 5 pages, fenêtres fixes |
|---|---|---|---|
| Dommages tous accidents | 43, 71 | 43, 39, 38, 34, 10 | 43, 39, 34, 38, 10 |
| Bris des feux arrière | 40 | 11, 40, 80, 54, 9 | 11, 40, 23, 45, 38 |
| Franchise | 49 | 51, 49, 52, 50, 55 | 51, 49, 52, 50, 55 |
| Délais de déclaration | 53, 54 | 64, 53, 57, 55, 54 | 64, 53, 57, 55, 54 |
| Formules de garanties | 71 | 6, 10, 71, 9, 11 | 6, 10, 71, 9, 11 |
| Exclusion liée à l’alcool | 43 | 48, 23, 43, 42, 21 | 48, 48, 43, 23, 42 |
| Conditions particulières et dommages tous accidents | 43, 71 | 43, 74, 8, 18, 39 | 43, 74, 8, 18, 39 |
| Indemnisation réparations | 55, 56, 57 | 7, 56, 57, 45, 9 | 56, 7, 56, 57, 45 |

## Limites et suite

Les pages pertinentes sont des annotations manuelles sur seulement huit requêtes ; les requêtes n’ont pas été produites par plusieurs évaluateurs. L’index a été évalué avec un petit jeu fixe ; les textes de pages dépassant la limite de contexte effective du modèle d’embedding peuvent être tronqués. Étape suivante : élargir les questions et faire annoter les pages par une seconde personne, puis compléter avec une mesure de génération (fidélité aux clauses et abstention quand les Conditions particulières manquent).
