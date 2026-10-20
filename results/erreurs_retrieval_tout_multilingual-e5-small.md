# Analyse d'erreurs du retrieval

Requêtes dont aucun article attendu n'est dans le chunk classé 1er. Rang = position du premier bon chunk dans le classement complet.

## Taille fixe 500/50 + BM25

19 requête(s) sur 32 pas en 1re position.

| Requête | Texte | Attendus | Rang réel | Classé 1er à la place |
|---|---|---|---|---|
| Q04 | Quelle franchise en cas de responsabilité partielle ? | 21 | 3 | R421-3, R421-4 |
| Q05 | Montant de la franchise pour un remplacement de pare-brise | 20 | 2 | 6, 7, 8, 9, 10 |
| Q07 | Je fais du VTC avec ma voiture personnelle, suis-je couvert ? | 15 | 2 | D113-7, R*113-10 |
| Q09 | Quels documents envoyer pour déclarer un sinistre ? | 18 | 7 | L113-1, L113-2 |
| Q10 | Quand l'assureur envoie-t-il un expert ? | 19 | 6 | L121-2, L121-3, L121-4 |
| Q11 | Facture de réparation gonflée, que risque l'assuré ? | 23, 25 | 5 | 18, 19, 20, 21 |
| Q15 | Le conducteur responsable est blessé, est-il indemnisé ? | 12, R211-8 | 7 | A211-11-annexe |
| Q17 | Accident survenu au Maroc, suis-je assuré ? | 3, L211-4 | 36 | A121-1-annexe-4, A121-1-annexe-5, A121-1-annexe-6 |
| Q18 | Qui doit valider un refus de prise en charge ? | 24 | 5 | R421-20 |
| Q21 | L'assuré a menti sur l'usage du véhicule à la souscription, le contrat est-il nul ? | L113-8, L113-9 | 5 | L211-28, D211-1 |
| Q23 | L'assuré utilise désormais son véhicule pour une activité rémunérée sans l'avoir déclaré | L113-2, L113-4, 15 | 13 | A211-11-annexe |
| Q24 | L'indemnité peut-elle être supérieure à la valeur du véhicule ? | L121-1, 6 | 3 | A125-6-4-2, A125-6-4-3, A125-6-5, L126-1 |
| Q25 | Dans quel délai l'assuré peut-il agir en justice contre son assureur ? | L114-1 | 13 | L121-11, L121-12, L121-13 |
| Q26 | Délai pour faire une proposition d'indemnisation après une expertise | L121-18 | 2 | L125-2 |
| Q27 | La victime peut-elle réclamer directement l'indemnisation à l'assureur du responsable ? | L124-3 | 40 | A211-11-annexe |
| Q28 | Délai pour présenter une offre d'indemnité à une victime blessée | L211-9 | 3 | R211-29, R211-30, R211-31, R211-32 |
| Q30 | L'assuré peut-il choisir librement son garagiste ? | L211-5-1 | 3 | L127-2-3, L127-3, L127-4 |
| Q31 | La franchise peut-elle être opposée à la victime d'un accident ? | R211-13 | 161 | A211-11, A211-11-annexe |
| Q32 | Accident pendant une course automobile, l'assureur peut-il refuser ? | R211-11, 14 | 107 | R421-68, R421-69 |

## Taille fixe 500/50 + Dense (multilingual-e5-small)

22 requête(s) sur 32 pas en 1re position.

| Requête | Texte | Attendus | Rang réel | Classé 1er à la place |
|---|---|---|---|---|
| Q02 | Que se passe-t-il si le conducteur n'est pas désigné au contrat ? | 16 | 2 | R211-8, R211-10 |
| Q06 | Un accident en état d'ivresse est-il indemnisé ? | 14, L211-6 | 21 | L211-9, L211-10 |
| Q08 | Sortie de route sans autre véhicule avec la garantie collision | 7 | 3 | A211-11-annexe |
| Q09 | Quels documents envoyer pour déclarer un sinistre ? | 18 | 2 | A211-11-annexe |
| Q10 | Quand l'assureur envoie-t-il un expert ? | 19 | 5 | A211-11-annexe |
| Q11 | Facture de réparation gonflée, que risque l'assuré ? | 23, 25 | 50 | A211-11-annexe |
| Q13 | Dommages causés par la grêle | 10 | 6 | R125-7, A125-2 |
| Q14 | Délai de déclaration après une inondation reconnue catastrophe naturelle | 17, 11 | 2 | L125-1 |
| Q15 | Le conducteur responsable est blessé, est-il indemnisé ? | 12, R211-8 | 2 | A211-11-annexe |
| Q17 | Accident survenu au Maroc, suis-je assuré ? | 3, L211-4 | 16 | A211-11-annexe |
| Q18 | Qui doit valider un refus de prise en charge ? | 24 | 37 | R421-20 |
| Q20 | Remorquage après accident | 13 | 17 | L211-7-1, L211-8, L211-9 |
| Q21 | L'assuré a menti sur l'usage du véhicule à la souscription, le contrat est-il nul ? | L113-8, L113-9 | 18 | L112-2-1 |
| Q22 | Oubli de bonne foi dans la déclaration du risque découvert après le sinistre | L113-9 | 6 | R421-20 |
| Q23 | L'assuré utilise désormais son véhicule pour une activité rémunérée sans l'avoir déclaré | L113-2, L113-4, 15 | 10 | R211-8, R211-10 |
| Q24 | L'indemnité peut-elle être supérieure à la valeur du véhicule ? | L121-1, 6 | 9 | R421-1, R421-2 |
| Q25 | Dans quel délai l'assuré peut-il agir en justice contre son assureur ? | L114-1 | 27 | A211-11-annexe |
| Q26 | Délai pour faire une proposition d'indemnisation après une expertise | L121-18 | 3 | A211-11-annexe |
| Q27 | La victime peut-elle réclamer directement l'indemnisation à l'assureur du responsable ? | L124-3 | 85 | R421-20 |
| Q28 | Délai pour présenter une offre d'indemnité à une victime blessée | L211-9 | 3 | A211-11-annexe |
| Q31 | La franchise peut-elle être opposée à la victime d'un accident ? | R211-13 | 20 | 18, 19, 20, 21 |
| Q32 | Accident pendant une course automobile, l'assureur peut-il refuser ? | R211-11, 14 | 60 | L211-1 |

## Taille fixe 500/50 + Hybride (RRF)

16 requête(s) sur 32 pas en 1re position.

| Requête | Texte | Attendus | Rang réel | Classé 1er à la place |
|---|---|---|---|---|
| Q05 | Montant de la franchise pour un remplacement de pare-brise | 20 | 2 | 6, 7, 8, 9, 10 |
| Q06 | Un accident en état d'ivresse est-il indemnisé ? | 14, L211-6 | 6 | A211-11-annexe |
| Q09 | Quels documents envoyer pour déclarer un sinistre ? | 18 | 2 | R127-1, L128-1 |
| Q10 | Quand l'assureur envoie-t-il un expert ? | 19 | 6 | L121-18 |
| Q11 | Facture de réparation gonflée, que risque l'assuré ? | 23, 25 | 16 | 18, 19, 20, 21 |
| Q15 | Le conducteur responsable est blessé, est-il indemnisé ? | 12, R211-8 | 7 | A211-11-annexe |
| Q17 | Accident survenu au Maroc, suis-je assuré ? | 3, L211-4 | 39 | R211-8, R211-10 |
| Q18 | Qui doit valider un refus de prise en charge ? | 24 | 5 | R421-20 |
| Q20 | Remorquage après accident | 13 | 2 | A211-11-annexe, L421-1 |
| Q21 | L'assuré a menti sur l'usage du véhicule à la souscription, le contrat est-il nul ? | L113-8, L113-9 | 2 | 14, 15, 16 |
| Q23 | L'assuré utilise désormais son véhicule pour une activité rémunérée sans l'avoir déclaré | L113-2, L113-4, 15 | 4 | R211-14-0-1, R211-14 |
| Q24 | L'indemnité peut-elle être supérieure à la valeur du véhicule ? | L121-1, 6 | 2 | A211-11, A211-11-annexe |
| Q25 | Dans quel délai l'assuré peut-il agir en justice contre son assureur ? | L114-1 | 12 | L211-11, L211-12, L211-13, L211-14 |
| Q27 | La victime peut-elle réclamer directement l'indemnisation à l'assureur du responsable ? | L124-3 | 55 | R421-20 |
| Q31 | La franchise peut-elle être opposée à la victime d'un accident ? | R211-13 | 54 | R421-20 |
| Q32 | Accident pendant une course automobile, l'assureur peut-il refuser ? | R211-11, 14 | 104 | R421-68, R421-69 |

## Par article + BM25

14 requête(s) sur 32 pas en 1re position.

| Requête | Texte | Attendus | Rang réel | Classé 1er à la place |
|---|---|---|---|---|
| Q05 | Montant de la franchise pour un remplacement de pare-brise | 20 | 2 | 8 — Bris de glace |
| Q07 | Je fais du VTC avec ma voiture personnelle, suis-je couvert ? | 15 | 2 | D113-7 — Obligations de l'assureur et de l'assuré |
| Q09 | Quels documents envoyer pour déclarer un sinistre ? | 18 | 60 | 17 — Délais de déclaration |
| Q11 | Facture de réparation gonflée, que risque l'assuré ? | 23, 25 | 2 | 19 — Expertise et évaluation des dommages |
| Q12 | Dans quels cas un dossier doit passer en investigation ? | 25 | 2 | 24 — Circuit de traitement d'un dossier |
| Q17 | Accident survenu au Maroc, suis-je assuré ? | 3, L211-4 | 50 | L421-1 — Dispositions générales |
| Q18 | Qui doit valider un refus de prise en charge ? | 24 | 5 | R421-20 — Dispositions applicables à l'indemnisation des dommages aux biens |
| Q19 | Jeune conducteur qui emprunte la voiture, franchise ? | 16, 20 | 2 | 2 — Définitions |
| Q23 | L'assuré utilise désormais son véhicule pour une activité rémunérée sans l'avoir déclaré | L113-2, L113-4, 15 | 10 | R113-13 — Obligations de l'assureur et de l'assuré |
| Q25 | Dans quel délai l'assuré peut-il agir en justice contre son assureur ? | L114-1 | 2 | L211-12 — Procédures d'indemnisation |
| Q27 | La victime peut-elle réclamer directement l'indemnisation à l'assureur du responsable ? | L124-3 | 38 | A211-11-annexe — Procédures d'indemnisation |
| Q30 | L'assuré peut-il choisir librement son garagiste ? | L211-5-1 | 3 | L127-3 — L'assurance de protection juridique |
| Q31 | La franchise peut-elle être opposée à la victime d'un accident ? | R211-13 | 372 | A211-11-annexe — Procédures d'indemnisation |
| Q32 | Accident pendant une course automobile, l'assureur peut-il refuser ? | R211-11, 14 | 342 | A211-11-annexe — Procédures d'indemnisation |

## Par article + Dense (multilingual-e5-small)

13 requête(s) sur 32 pas en 1re position.

| Requête | Texte | Attendus | Rang réel | Classé 1er à la place |
|---|---|---|---|---|
| Q03 | Quel est le délai pour déclarer un vol ? | 17, L113-2 | 2 | 22 — Délai de règlement |
| Q04 | Quelle franchise en cas de responsabilité partielle ? | 21 | 3 | D125-5-8 — Les franchises |
| Q05 | Montant de la franchise pour un remplacement de pare-brise | 20 | 2 | 8 — Bris de glace |
| Q11 | Facture de réparation gonflée, que risque l'assuré ? | 23, 25 | 6 | 5 — Défense pénale et recours |
| Q16 | Conduite sans permis valide | 14, R211-10 | 3 | 16 — Conducteur non désigné et prêt du volant |
| Q17 | Accident survenu au Maroc, suis-je assuré ? | 3, L211-4 | 14 | A211-11-annexe — Procédures d'indemnisation |
| Q18 | Qui doit valider un refus de prise en charge ? | 24 | 60 | L211-12 — Procédures d'indemnisation |
| Q20 | Remorquage après accident | 13 | 2 | L211-8 — Champ d'application : victimes d'un accident de la circulation impliquant un véhicule |
| Q21 | L'assuré a menti sur l'usage du véhicule à la souscription, le contrat est-il nul ? | L113-8, L113-9 | 14 | L211-7-1 — Nullité du contrat inopposable aux victimes |
| Q23 | L'assuré utilise désormais son véhicule pour une activité rémunérée sans l'avoir déclaré | L113-2, L113-4, 15 | 4 | R211-14-0-1 — Le contrôle des véhicules immatriculés soumis à obligation d'assurance |
| Q25 | Dans quel délai l'assuré peut-il agir en justice contre son assureur ? | L114-1 | 28 | L211-12 — Procédures d'indemnisation |
| Q27 | La victime peut-elle réclamer directement l'indemnisation à l'assureur du responsable ? | L124-3 | 37 | L211-19 — Aggravation du dommage de la victime |
| Q32 | Accident pendant une course automobile, l'assureur peut-il refuser ? | R211-11, 14 | 31 | 5 — Défense pénale et recours |

## Par article + Hybride (RRF)

13 requête(s) sur 32 pas en 1re position.

| Requête | Texte | Attendus | Rang réel | Classé 1er à la place |
|---|---|---|---|---|
| Q05 | Montant de la franchise pour un remplacement de pare-brise | 20 | 2 | 8 — Bris de glace |
| Q09 | Quels documents envoyer pour déclarer un sinistre ? | 18 | 9 | 17 — Délais de déclaration |
| Q11 | Facture de réparation gonflée, que risque l'assuré ? | 23, 25 | 20 | 19 — Expertise et évaluation des dommages |
| Q12 | Dans quels cas un dossier doit passer en investigation ? | 25 | 2 | 24 — Circuit de traitement d'un dossier |
| Q17 | Accident survenu au Maroc, suis-je assuré ? | 3, L211-4 | 20 | L451-1 — Organisme d'information |
| Q18 | Qui doit valider un refus de prise en charge ? | 24 | 8 | R421-20 — Dispositions applicables à l'indemnisation des dommages aux biens |
| Q19 | Jeune conducteur qui emprunte la voiture, franchise ? | 16, 20 | 2 | 2 — Définitions |
| Q21 | L'assuré a menti sur l'usage du véhicule à la souscription, le contrat est-il nul ? | L113-8, L113-9 | 2 | 15 — Exclusions liées à l'usage du véhicule |
| Q23 | L'assuré utilise désormais son véhicule pour une activité rémunérée sans l'avoir déclaré | L113-2, L113-4, 15 | 3 | R211-14-0-1 — Le contrôle des véhicules immatriculés soumis à obligation d'assurance |
| Q25 | Dans quel délai l'assuré peut-il agir en justice contre son assureur ? | L114-1 | 2 | L211-12 — Procédures d'indemnisation |
| Q27 | La victime peut-elle réclamer directement l'indemnisation à l'assureur du responsable ? | L124-3 | 31 | L211-19 — Aggravation du dommage de la victime |
| Q31 | La franchise peut-elle être opposée à la victime d'un accident ? | R211-13 | 44 | 6 — Dommages tous accidents |
| Q32 | Accident pendant une course automobile, l'assureur peut-il refuser ? | R211-11, 14 | 99 | R421-68 — Dispositions particulières applicables aux accidents d'automobile survenus à l'étranger |

## Tableau croisé — Par article

Requêtes pas en 1re position, selon le ou les retrievers qui les ratent.

| Ratée par | Nb | Requêtes |
|---|---|---|
| BM25 seulement | 2 | Q07, Q30 |
| Dense (multilingual-e5-small) seulement | 4 | Q03, Q04, Q16, Q20 |
| Hybride (RRF) seulement | 0 | — |
| Les trois | 8 | Q05, Q11, Q17, Q18, Q23, Q25, Q27, Q32 |
