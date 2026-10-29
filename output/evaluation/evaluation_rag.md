# Évaluation du retrieval RAG

**Date :** 28 octobre 2026  
**Corpus :** Conditions générales AXA France « Mon Auto », septembre 2026, pages 5–103.  
**Modèle d’embeddings :** `nomic-embed-text:latest`, exécuté localement avec Ollama.  
**Reproduction :** `python output/evaluation/evaluate_rag.py --ollama --model nomic-embed-text:latest` (Ollama doit être lancé).

## Protocole

Seize requêtes couvrent les garanties, les exclusions, les franchises, les formalités, l’assistance et l’indemnisation. Les pages de référence ont été annotées manuellement à partir du contrat. Le test compare 99 passages correspondant aux pages complètes et 131 passages constitués de fenêtres de 500 mots avec 50 mots de chevauchement, sans franchir les limites de page. Pour chaque requête, le classement renvoie les cinq passages les mieux notés. Une requête est un hit si au moins une page pertinente annotée apparaît dans ce top 5.

Deux méthodes sont comparées : un score lexical simple (termes de la requête présents dans le passage) et les embeddings Ollama classés par similarité cosinus. Les métriques sont Hit@5 et MRR@5, calculées sur les pages pertinentes.

## Résultats

| Méthode | Segmentation | Passages | Hit@5 | MRR@5 |
|---|---|---:|---:|---:|
| Lexicale | Pages complètes | 99 | 0,812 (13/16) | 0,658 |
| Lexicale | Fenêtres 500 mots / chevauchement 50 | 131 | 0,812 (13/16) | 0,661 |
| Nomic + cosinus | Pages complètes | 99 | 0,938 (15/16) | 0,604 |
| Nomic + cosinus | Fenêtres 500 mots / chevauchement 50 | 131 | 0,938 (15/16) | 0,596 |

Sur ce jeu, le modèle d’embeddings trouve une page pertinente dans le top 5 pour 15 requêtes sur 16 ; le score lexical le fait pour 13 sur 16. Le découpage en fenêtres ne modifie pas Hit@5. Son MRR est pratiquement identique pour le score lexical (+0,003) et légèrement plus faible avec les embeddings (−0,008). Les fenêtres ont donc été retenues dans le backend pour borner la longueur transmise au modèle, et non parce que ce petit benchmark démontre une meilleure pertinence.

## Requêtes et pages annotées

| # | Question | Pages pertinentes |
|---:|---|---|
| 1 | Garantie dommages tous accidents et dommages au véhicule | 43, 71 |
| 2 | Les feux arrière sont-ils couverts par le bris de glace ? | 40 |
| 3 | Part de l’indemnité restant à la charge de l’assuré (franchise) | 49 |
| 4 | Délais et formalités de déclaration d’un sinistre | 53, 54 |
| 5 | Garanties des différentes formules auto | 71 |
| 6 | Exclusions en cas d’état alcoolique ou de stupéfiants | 43 |
| 7 | La garantie dommages tous accidents dépend-elle des Conditions particulières ? | 43, 71 |
| 8 | Indemnisation des réparations du véhicule | 55, 56, 57 |
| 9 | Assistance et dépannage en cas de panne | 31 |
| 10 | Dommages causés aux tiers par la responsabilité civile | 55 |
| 11 | Franchise pour catastrophe naturelle | 47 |
| 12 | Dommages au véhicule après effraction ou tentative de vol | 41 |
| 13 | Faut-il déclarer le sinistre avant toute réparation ? | 53 |
| 14 | Sanctions en cas de non-respect des formalités de déclaration | 54 |
| 15 | Paiement au garage partenaire | 57 |
| 16 | Indemnisation si réparation dans un garage non partenaire | 56 |

## Limites et interprétation

Ce test mesure le classement de passages, pas la justesse de la réponse générée ni la validité d’une décision d’assurance. Les 16 requêtes et leurs références ont été préparées par une seule personne, sur un seul contrat. Il n’y a pas de questions paraphrasées par plusieurs évaluateurs, de test de robustesse linguistique, ni d’évaluation de la fidélité des réponses aux clauses citées. Les passages d’une même page peuvent occuper plusieurs places du top 5 ; les scores reflètent donc un retrieval de passages, pas une diversité de pages. Les résultats doivent être reproduits sur un corpus plus large et complétés par une évaluation de génération, d’abstention et de dossiers annotés avant tout usage opérationnel.
