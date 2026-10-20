# Analyse d'erreurs du retrieval

Requêtes dont aucun article attendu n'est dans le chunk classé 1er. Rang = position du premier bon chunk dans le classement complet.

## Taille fixe 500/50 + BM25 (stem)

20 requête(s) sur 32 pas en 1re position.

| Requête | Texte | Attendus | Rang réel | Classé 1er à la place |
|---|---|---|---|---|
| Q02 | Que se passe-t-il si le conducteur n'est pas désigné au contrat ? | 16 | 3 | A121-1-annexe-9, A121-1-annexe-10, A121-1-annexe-11, A121-1-annexe-12 |
| Q04 | Quelle franchise en cas de responsabilité partielle ? | 21 | 4 | R421-3, R421-4 |
| Q05 | Montant de la franchise pour un remplacement de pare-brise | 20 | 2 | 6, 7, 8, 9, 10 |
| Q07 | Je fais du VTC avec ma voiture personnelle, suis-je couvert ? | 15 | 6 | D113-7, R*113-10 |
| Q09 | Quels documents envoyer pour déclarer un sinistre ? | 18 | 19 | D112-5, R112-6, R112-7 |
| Q10 | Quand l'assureur envoie-t-il un expert ? | 19 | 6 | L114-1, L114-2, L114-3, R114-1 |
| Q11 | Facture de réparation gonflée, que risque l'assuré ? | 23, 25 | 7 | R125-6-1, R125-7 |
| Q14 | Délai de déclaration après une inondation reconnue catastrophe naturelle | 17, 11 | 2 | L125-1-2, L125-2 |
| Q17 | Accident survenu au Maroc, suis-je assuré ? | 3, L211-4 | 25 | L421-9 |
| Q18 | Qui doit valider un refus de prise en charge ? | 24 | 3 | R211-21-2, R211-21-3, R211-21-4 |
| Q19 | Jeune conducteur qui emprunte la voiture, franchise ? | 16, 20 | 2 | A211-1-2, A211-1-3, A211-3 |
| Q21 | L'assuré a menti sur l'usage du véhicule à la souscription, le contrat est-il nul ? | L113-8, L113-9 | 2 | R250-2, R250-3 |
| Q24 | L'indemnité peut-elle être supérieure à la valeur du véhicule ? | L121-1, 6 | 4 | R125-6-1 |
| Q25 | Dans quel délai l'assuré peut-il agir en justice contre son assureur ? | L114-1 | 10 | L124-5 |
| Q26 | Délai pour faire une proposition d'indemnisation après une expertise | L121-18 | 4 | L125-2 |
| Q27 | La victime peut-elle réclamer directement l'indemnisation à l'assureur du responsable ? | L124-3 | 3 | R421-8, R421-9 |
| Q28 | Délai pour présenter une offre d'indemnité à une victime blessée | L211-9 | 2 | L211-11, L211-12, L211-13, L211-14 |
| Q30 | L'assuré peut-il choisir librement son garagiste ? | L211-5-1 | 3 | L127-2-3, L127-3, L127-4 |
| Q31 | La franchise peut-elle être opposée à la victime d'un accident ? | R211-13 | 3 | R421-3, R421-4 |
| Q32 | Accident pendant une course automobile, l'assureur peut-il refuser ? | R211-11, 14 | 10 | R421-68, R421-69 |

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

14 requête(s) sur 32 pas en 1re position.

| Requête | Texte | Attendus | Rang réel | Classé 1er à la place |
|---|---|---|---|---|
| Q05 | Montant de la franchise pour un remplacement de pare-brise | 20 | 2 | 6, 7, 8, 9, 10 |
| Q06 | Un accident en état d'ivresse est-il indemnisé ? | 14, L211-6 | 5 | L211-9, L211-10 |
| Q09 | Quels documents envoyer pour déclarer un sinistre ? | 18 | 5 | R421-4, R421-5, R421-6 |
| Q10 | Quand l'assureur envoie-t-il un expert ? | 19 | 7 | A211-11-annexe |
| Q11 | Facture de réparation gonflée, que risque l'assuré ? | 23, 25 | 17 | 18, 19, 20, 21 |
| Q14 | Délai de déclaration après une inondation reconnue catastrophe naturelle | 17, 11 | 2 | L125-1 |
| Q15 | Le conducteur responsable est blessé, est-il indemnisé ? | 12, R211-8 | 2 | A211-11-annexe |
| Q17 | Accident survenu au Maroc, suis-je assuré ? | 3, L211-4 | 13 | R211-8, R211-10 |
| Q18 | Qui doit valider un refus de prise en charge ? | 24 | 9 | R421-20 |
| Q25 | Dans quel délai l'assuré peut-il agir en justice contre son assureur ? | L114-1 | 4 | R421-20, R421-37 |
| Q26 | Délai pour faire une proposition d'indemnisation après une expertise | L121-18 | 2 | L113-4, L113-5, L113-5-1, L113-6 |
| Q27 | La victime peut-elle réclamer directement l'indemnisation à l'assureur du responsable ? | L124-3 | 25 | L211-9, L211-10 |
| Q31 | La franchise peut-elle être opposée à la victime d'un accident ? | R211-13 | 4 | 18, 19, 20, 21 |
| Q32 | Accident pendant une course automobile, l'assureur peut-il refuser ? | R211-11, 14 | 17 | R421-68, R421-69 |

## Par article + BM25 (stem)

14 requête(s) sur 32 pas en 1re position.

| Requête | Texte | Attendus | Rang réel | Classé 1er à la place |
|---|---|---|---|---|
| Q02 | Que se passe-t-il si le conducteur n'est pas désigné au contrat ? | 16 | 2 | A121-1-annexe-10 — Clause type bonus-malus, article 10 |
| Q03 | Quel est le délai pour déclarer un vol ? | 17, L113-2 | 2 | 9 — Vol et tentative de vol |
| Q04 | Quelle franchise en cas de responsabilité partielle ? | 21 | 2 | 20 — Tableau des franchises |
| Q05 | Montant de la franchise pour un remplacement de pare-brise | 20 | 2 | 8 — Bris de glace |
| Q09 | Quels documents envoyer pour déclarer un sinistre ? | 18 | 21 | 23 — Fausse déclaration et fraude |
| Q10 | Quand l'assureur envoie-t-il un expert ? | 19 | 2 | L114-2 — Interruption de la prescription (désignation d'experts, lettre recommandée) |
| Q11 | Facture de réparation gonflée, que risque l'assuré ? | 23, 25 | 10 | R125-6-1 — Obligations de l'assureur et de l'assuré |
| Q12 | Dans quels cas un dossier doit passer en investigation ? | 25 | 2 | 24 — Circuit de traitement d'un dossier |
| Q17 | Accident survenu au Maroc, suis-je assuré ? | 3, L211-4 | 106 | L122-4 — Les assurances contre l'incendie |
| Q19 | Jeune conducteur qui emprunte la voiture, franchise ? | 16, 20 | 2 | A211-3 — Franchises, exclusions de garantie et déchéances |
| Q25 | Dans quel délai l'assuré peut-il agir en justice contre son assureur ? | L114-1 | 8 | L211-12 — Procédures d'indemnisation |
| Q27 | La victime peut-elle réclamer directement l'indemnisation à l'assureur du responsable ? | L124-3 | 8 | A211-11-annexe — Procédures d'indemnisation |
| Q30 | L'assuré peut-il choisir librement son garagiste ? | L211-5-1 | 3 | 13 — Assistance |
| Q32 | Accident pendant une course automobile, l'assureur peut-il refuser ? | R211-11, 14 | 8 | R250-2 — Dispositions relatives au Bureau central de tarification |

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

12 requête(s) sur 32 pas en 1re position.

| Requête | Texte | Attendus | Rang réel | Classé 1er à la place |
|---|---|---|---|---|
| Q03 | Quel est le délai pour déclarer un vol ? | 17, L113-2 | 3 | 9 — Vol et tentative de vol |
| Q05 | Montant de la franchise pour un remplacement de pare-brise | 20 | 2 | 8 — Bris de glace |
| Q09 | Quels documents envoyer pour déclarer un sinistre ? | 18 | 6 | 23 — Fausse déclaration et fraude |
| Q11 | Facture de réparation gonflée, que risque l'assuré ? | 23, 25 | 19 | R125-6-1 — Obligations de l'assureur et de l'assuré |
| Q12 | Dans quels cas un dossier doit passer en investigation ? | 25 | 2 | 24 — Circuit de traitement d'un dossier |
| Q17 | Accident survenu au Maroc, suis-je assuré ? | 3, L211-4 | 34 | L451-1 — Organisme d'information |
| Q18 | Qui doit valider un refus de prise en charge ? | 24 | 6 | R421-20 — Dispositions applicables à l'indemnisation des dommages aux biens |
| Q21 | L'assuré a menti sur l'usage du véhicule à la souscription, le contrat est-il nul ? | L113-8, L113-9 | 2 | 15 — Exclusions liées à l'usage du véhicule |
| Q23 | L'assuré utilise désormais son véhicule pour une activité rémunérée sans l'avoir déclaré | L113-2, L113-4, 15 | 2 | R211-14-0-1 — Le contrôle des véhicules immatriculés soumis à obligation d'assurance |
| Q25 | Dans quel délai l'assuré peut-il agir en justice contre son assureur ? | L114-1 | 4 | L211-12 — Procédures d'indemnisation |
| Q27 | La victime peut-elle réclamer directement l'indemnisation à l'assureur du responsable ? | L124-3 | 12 | A211-11-annexe — Procédures d'indemnisation |
| Q32 | Accident pendant une course automobile, l'assureur peut-il refuser ? | R211-11, 14 | 6 | L113-12-2 — Obligations de l'assureur et de l'assuré |

## Tableau croisé — Par article

Requêtes pas en 1re position, selon le ou les retrievers qui les ratent.

| Ratée par | Nb | Requêtes |
|---|---|---|
| BM25 (stem) seulement | 4 | Q02, Q10, Q19, Q30 |
| Dense (multilingual-e5-small) seulement | 2 | Q16, Q20 |
| Hybride (RRF) seulement | 0 | — |
| Les trois | 7 | Q03, Q05, Q11, Q17, Q25, Q27, Q32 |
