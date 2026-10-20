# Analyse d'erreurs du retrieval

Requêtes dont aucun article attendu n'est dans le chunk classé 1er. Rang = position du premier bon chunk dans le classement complet.

## Par article + BM25

17 requête(s) sur 32 pas en 1re position.

| Requête | Texte | Attendus | Rang réel | Classé 1er à la place |
|---|---|---|---|---|
| Q05 | Montant de la franchise pour un remplacement de pare-brise | 20 | 2 | 8 — Bris de glace |
| Q09 | Quels documents envoyer pour déclarer un sinistre ? | 18 | 29 | 23 — Fausse déclaration et fraude |
| Q11 | Facture de réparation gonflée, que risque l'assuré ? | 23, 25 | 4 | 19 — Expertise et évaluation des dommages |
| Q12 | Dans quels cas un dossier doit passer en investigation ? | 25 | 2 | 24 — Circuit de traitement d'un dossier |
| Q15 | Le conducteur responsable est blessé, est-il indemnisé ? | 12, R211-8 | 2 | A211-11-annexe — Procédures d'indemnisation |
| Q17 | Accident survenu au Maroc, suis-je assuré ? | 3, L211-4 | 63 | L421-1 — Dispositions générales |
| Q18 | Qui doit valider un refus de prise en charge ? | 24 | 5 | R421-20 — Dispositions applicables à l'indemnisation des dommages aux biens |
| Q19 | Jeune conducteur qui emprunte la voiture, franchise ? | 16, 20 | 2 | 2 — Définitions |
| Q21 | L'assuré a menti sur l'usage du véhicule à la souscription, le contrat est-il nul ? | L113-8, L113-9 | absent | L211-1-1 — Véhicule irréparable : conditions de résiliation du contrat |
| Q22 | Oubli de bonne foi dans la déclaration du risque découvert après le sinistre | L113-9 | absent | 23 — Fausse déclaration et fraude |
| Q23 | L'assuré utilise désormais son véhicule pour une activité rémunérée sans l'avoir déclaré | L113-2, L113-4, 15 | 8 | R211-14-0-1 — Le contrôle des véhicules immatriculés soumis à obligation d'assurance |
| Q24 | L'indemnité peut-elle être supérieure à la valeur du véhicule ? | L121-1, 6 | 2 | L211-4 — Étendue territoriale de la garantie et personnes transportées |
| Q25 | Dans quel délai l'assuré peut-il agir en justice contre son assureur ? | L114-1 | absent | L211-12 — Procédures d'indemnisation |
| Q26 | Délai pour faire une proposition d'indemnisation après une expertise | L121-18 | absent | D211-1 — Personnes assujetties |
| Q27 | La victime peut-elle réclamer directement l'indemnisation à l'assureur du responsable ? | L124-3 | absent | A211-11-annexe — Procédures d'indemnisation |
| Q31 | La franchise peut-elle être opposée à la victime d'un accident ? | R211-13 | 156 | A211-11-annexe — Procédures d'indemnisation |
| Q32 | Accident pendant une course automobile, l'assureur peut-il refuser ? | R211-11, 14 | 201 | A211-11-annexe — Procédures d'indemnisation |

## Par article + Dense (multilingual-e5-small)

14 requête(s) sur 32 pas en 1re position.

| Requête | Texte | Attendus | Rang réel | Classé 1er à la place |
|---|---|---|---|---|
| Q03 | Quel est le délai pour déclarer un vol ? | 17, L113-2 | 2 | 22 — Délai de règlement |
| Q05 | Montant de la franchise pour un remplacement de pare-brise | 20 | 2 | 8 — Bris de glace |
| Q11 | Facture de réparation gonflée, que risque l'assuré ? | 23, 25 | 4 | 5 — Défense pénale et recours |
| Q16 | Conduite sans permis valide | 14, R211-10 | 3 | 16 — Conducteur non désigné et prêt du volant |
| Q17 | Accident survenu au Maroc, suis-je assuré ? | 3, L211-4 | 13 | A211-11-annexe — Procédures d'indemnisation |
| Q18 | Qui doit valider un refus de prise en charge ? | 24 | 43 | L211-12 — Procédures d'indemnisation |
| Q20 | Remorquage après accident | 13 | 2 | L211-8 — Champ d'application : victimes d'un accident de la circulation impliquant un véhicule |
| Q21 | L'assuré a menti sur l'usage du véhicule à la souscription, le contrat est-il nul ? | L113-8, L113-9 | absent | L211-7-1 — Nullité du contrat inopposable aux victimes |
| Q22 | Oubli de bonne foi dans la déclaration du risque découvert après le sinistre | L113-9 | absent | R421-20 — Dispositions applicables à l'indemnisation des dommages aux biens |
| Q23 | L'assuré utilise désormais son véhicule pour une activité rémunérée sans l'avoir déclaré | L113-2, L113-4, 15 | 4 | R211-14-0-1 — Le contrôle des véhicules immatriculés soumis à obligation d'assurance |
| Q25 | Dans quel délai l'assuré peut-il agir en justice contre son assureur ? | L114-1 | absent | L211-12 — Procédures d'indemnisation |
| Q26 | Délai pour faire une proposition d'indemnisation après une expertise | L121-18 | absent | R211-34 — Procédures d'indemnisation |
| Q27 | La victime peut-elle réclamer directement l'indemnisation à l'assureur du responsable ? | L124-3 | absent | L211-19 — Aggravation du dommage de la victime |
| Q32 | Accident pendant une course automobile, l'assureur peut-il refuser ? | R211-11, 14 | 28 | 5 — Défense pénale et recours |

## Par article + Hybride (RRF)

16 requête(s) sur 32 pas en 1re position.

| Requête | Texte | Attendus | Rang réel | Classé 1er à la place |
|---|---|---|---|---|
| Q05 | Montant de la franchise pour un remplacement de pare-brise | 20 | 2 | 8 — Bris de glace |
| Q09 | Quels documents envoyer pour déclarer un sinistre ? | 18 | 7 | 17 — Délais de déclaration |
| Q11 | Facture de réparation gonflée, que risque l'assuré ? | 23, 25 | 19 | 5 — Défense pénale et recours |
| Q12 | Dans quels cas un dossier doit passer en investigation ? | 25 | 2 | 24 — Circuit de traitement d'un dossier |
| Q15 | Le conducteur responsable est blessé, est-il indemnisé ? | 12, R211-8 | 2 | A211-11-annexe — Procédures d'indemnisation |
| Q17 | Accident survenu au Maroc, suis-je assuré ? | 3, L211-4 | 23 | L451-1 — Organisme d'information |
| Q18 | Qui doit valider un refus de prise en charge ? | 24 | 6 | R421-20 — Dispositions applicables à l'indemnisation des dommages aux biens |
| Q19 | Jeune conducteur qui emprunte la voiture, franchise ? | 16, 20 | 2 | 2 — Définitions |
| Q21 | L'assuré a menti sur l'usage du véhicule à la souscription, le contrat est-il nul ? | L113-8, L113-9 | absent | 15 — Exclusions liées à l'usage du véhicule |
| Q22 | Oubli de bonne foi dans la déclaration du risque découvert après le sinistre | L113-9 | absent | 23 — Fausse déclaration et fraude |
| Q23 | L'assuré utilise désormais son véhicule pour une activité rémunérée sans l'avoir déclaré | L113-2, L113-4, 15 | 3 | R211-14-0-1 — Le contrôle des véhicules immatriculés soumis à obligation d'assurance |
| Q25 | Dans quel délai l'assuré peut-il agir en justice contre son assureur ? | L114-1 | absent | L211-12 — Procédures d'indemnisation |
| Q26 | Délai pour faire une proposition d'indemnisation après une expertise | L121-18 | absent | A211-11-annexe — Procédures d'indemnisation |
| Q27 | La victime peut-elle réclamer directement l'indemnisation à l'assureur du responsable ? | L124-3 | absent | L211-19 — Aggravation du dommage de la victime |
| Q31 | La franchise peut-elle être opposée à la victime d'un accident ? | R211-13 | 26 | 6 — Dommages tous accidents |
| Q32 | Accident pendant une course automobile, l'assureur peut-il refuser ? | R211-11, 14 | 82 | A211-11-annexe — Procédures d'indemnisation |

## Tableau croisé — Par article

Requêtes pas en 1re position, selon le ou les retrievers qui les ratent.

| Ratée par | Nb | Requêtes |
|---|---|---|
| BM25 seulement | 1 | Q24 |
| Dense (multilingual-e5-small) seulement | 3 | Q03, Q16, Q20 |
| Hybride (RRF) seulement | 0 | — |
| Les trois | 11 | Q05, Q11, Q17, Q18, Q21, Q22, Q23, Q25, Q26, Q27, Q32 |
