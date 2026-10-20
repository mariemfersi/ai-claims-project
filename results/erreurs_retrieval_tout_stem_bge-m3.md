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

## Taille fixe 500/50 + Dense (bge-m3)

21 requête(s) sur 32 pas en 1re position.

| Requête | Texte | Attendus | Rang réel | Classé 1er à la place |
|---|---|---|---|---|
| Q03 | Quel est le délai pour déclarer un vol ? | 17, L113-2 | 2 | 21, 22, 23, 24, 25 |
| Q04 | Quelle franchise en cas de responsabilité partielle ? | 21 | 11 | A125-6-4-2, A125-6-4-3, A125-6-5, L126-1 |
| Q05 | Montant de la franchise pour un remplacement de pare-brise | 20 | 2 | A125-6, A125-6-1 |
| Q06 | Un accident en état d'ivresse est-il indemnisé ? | 14, L211-6 | 7 | A211-11-annexe |
| Q07 | Je fais du VTC avec ma voiture personnelle, suis-je couvert ? | 15 | 17 | L211-1 |
| Q08 | Sortie de route sans autre véhicule avec la garantie collision | 7 | 7 | 14, 15, 16 |
| Q09 | Quels documents envoyer pour déclarer un sinistre ? | 18 | 2 | L125-1 |
| Q10 | Quand l'assureur envoie-t-il un expert ? | 19 | 4 | L121-18 |
| Q11 | Facture de réparation gonflée, que risque l'assuré ? | 23, 25 | 12 | R125-6-1 |
| Q13 | Dommages causés par la grêle | 10 | 3 | L121-13, L121-14, L121-15, L121-16 |
| Q14 | Délai de déclaration après une inondation reconnue catastrophe naturelle | 17, 11 | 15 | L125-1 |
| Q15 | Le conducteur responsable est blessé, est-il indemnisé ? | 12, R211-8 | 10 | A211-11-annexe |
| Q16 | Conduite sans permis valide | 14, R211-10 | 9 | L211-25, L211-26 |
| Q17 | Accident survenu au Maroc, suis-je assuré ? | 3, L211-4 | 2 | L424-8, L424-9 |
| Q18 | Qui doit valider un refus de prise en charge ? | 24 | 19 | R250-2 |
| Q20 | Remorquage après accident | 13 | 90 | L211-7-1, L211-8, L211-9 |
| Q23 | L'assuré utilise désormais son véhicule pour une activité rémunérée sans l'avoir déclaré | L113-2, L113-4, 15 | 11 | L211-25, L211-26 |
| Q24 | L'indemnité peut-elle être supérieure à la valeur du véhicule ? | L121-1, 6 | 2 | R128-4 |
| Q25 | Dans quel délai l'assuré peut-il agir en justice contre son assureur ? | L114-1 | 30 | A211-11-annexe |
| Q27 | La victime peut-elle réclamer directement l'indemnisation à l'assureur du responsable ? | L124-3 | 4 | A211-11-annexe |
| Q31 | La franchise peut-elle être opposée à la victime d'un accident ? | R211-13 | 16 | D125-5, D125-5-1, D125-5-2, D125-5-3 |

## Taille fixe 500/50 + Hybride (RRF)

18 requête(s) sur 32 pas en 1re position.

| Requête | Texte | Attendus | Rang réel | Classé 1er à la place |
|---|---|---|---|---|
| Q04 | Quelle franchise en cas de responsabilité partielle ? | 21 | 3 | R250-4-3, R250-5 |
| Q05 | Montant de la franchise pour un remplacement de pare-brise | 20 | 2 | 6, 7, 8, 9, 10 |
| Q07 | Je fais du VTC avec ma voiture personnelle, suis-je couvert ? | 15 | 2 | R211-14-0-1, R211-14 |
| Q09 | Quels documents envoyer pour déclarer un sinistre ? | 18 | 2 | L113-1, L113-2 |
| Q10 | Quand l'assureur envoie-t-il un expert ? | 19 | 3 | L121-18 |
| Q11 | Facture de réparation gonflée, que risque l'assuré ? | 23, 25 | 6 | R125-6-1 |
| Q14 | Délai de déclaration après une inondation reconnue catastrophe naturelle | 17, 11 | 8 | L125-1-2, L125-2 |
| Q15 | Le conducteur responsable est blessé, est-il indemnisé ? | 12, R211-8 | 5 | A211-11-annexe |
| Q16 | Conduite sans permis valide | 14, R211-10 | 3 | L211-25, L211-26 |
| Q17 | Accident survenu au Maroc, suis-je assuré ? | 3, L211-4 | 5 | L421-9 |
| Q18 | Qui doit valider un refus de prise en charge ? | 24 | 2 | R250-2 |
| Q20 | Remorquage après accident | 13 | 15 | A121-1-annexe-4, A121-1-annexe-5, A121-1-annexe-6 |
| Q23 | L'assuré utilise désormais son véhicule pour une activité rémunérée sans l'avoir déclaré | L113-2, L113-4, 15 | 4 | R211-14-0-1, R211-14 |
| Q25 | Dans quel délai l'assuré peut-il agir en justice contre son assureur ? | L114-1 | 11 | L113-4, L113-5, L113-5-1, L113-6 |
| Q26 | Délai pour faire une proposition d'indemnisation après une expertise | L121-18 | 2 | L125-2 |
| Q30 | L'assuré peut-il choisir librement son garagiste ? | L211-5-1 | 2 | L127-2-3, L127-3, L127-4 |
| Q31 | La franchise peut-elle être opposée à la victime d'un accident ? | R211-13 | 2 | 18, 19, 20, 21 |
| Q32 | Accident pendant une course automobile, l'assureur peut-il refuser ? | R211-11, 14 | 2 | R421-68, R421-69 |

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

## Par article + Dense (bge-m3)

12 requête(s) sur 32 pas en 1re position.

| Requête | Texte | Attendus | Rang réel | Classé 1er à la place |
|---|---|---|---|---|
| Q04 | Quelle franchise en cas de responsabilité partielle ? | 21 | 11 | D125-5-8 — Les franchises |
| Q06 | Un accident en état d'ivresse est-il indemnisé ? | 14, L211-6 | 8 | A211-11-annexe — Procédures d'indemnisation |
| Q08 | Sortie de route sans autre véhicule avec la garantie collision | 7 | 2 | R211-10 — Exclusions autorisées : conducteur sans permis valide ou n'ayant pas l'âge requis, transport de personnes |
| Q11 | Facture de réparation gonflée, que risque l'assuré ? | 23, 25 | 47 | L113-4 — Aggravation du risque en cours de contrat |
| Q13 | Dommages causés par la grêle | 10 | 2 | L121-13 — Dispositions générales |
| Q14 | Délai de déclaration après une inondation reconnue catastrophe naturelle | 17, 11 | 3 | L125-1 — Garantie catastrophes naturelles et constatation par arrêté interministériel |
| Q16 | Conduite sans permis valide | 14, R211-10 | 3 | R211-14 — Le contrôle de certains véhicules non immatriculés soumis à obligation d'assurance |
| Q18 | Qui doit valider un refus de prise en charge ? | 24 | 8 | R250-4-1 — Dispositions relatives au Bureau central de tarification |
| Q23 | L'assuré utilise désormais son véhicule pour une activité rémunérée sans l'avoir déclaré | L113-2, L113-4, 15 | 5 | 16 — Conducteur non désigné et prêt du volant |
| Q25 | Dans quel délai l'assuré peut-il agir en justice contre son assureur ? | L114-1 | 74 | L211-12 — Procédures d'indemnisation |
| Q27 | La victime peut-elle réclamer directement l'indemnisation à l'assureur du responsable ? | L124-3 | 2 | A211-11-annexe — Procédures d'indemnisation |
| Q32 | Accident pendant une course automobile, l'assureur peut-il refuser ? | R211-11, 14 | 3 | L211-7-1 — Nullité du contrat inopposable aux victimes |

## Par article + Hybride (RRF)

10 requête(s) sur 32 pas en 1re position.

| Requête | Texte | Attendus | Rang réel | Classé 1er à la place |
|---|---|---|---|---|
| Q03 | Quel est le délai pour déclarer un vol ? | 17, L113-2 | 2 | 9 — Vol et tentative de vol |
| Q04 | Quelle franchise en cas de responsabilité partielle ? | 21 | 2 | 20 — Tableau des franchises |
| Q06 | Un accident en état d'ivresse est-il indemnisé ? | 14, L211-6 | 2 | A211-11-annexe — Procédures d'indemnisation |
| Q09 | Quels documents envoyer pour déclarer un sinistre ? | 18 | 4 | 17 — Délais de déclaration |
| Q11 | Facture de réparation gonflée, que risque l'assuré ? | 23, 25 | 50 | R125-6-1 — Obligations de l'assureur et de l'assuré |
| Q12 | Dans quels cas un dossier doit passer en investigation ? | 25 | 2 | 24 — Circuit de traitement d'un dossier |
| Q14 | Délai de déclaration après une inondation reconnue catastrophe naturelle | 17, 11 | 2 | L125-1 — Garantie catastrophes naturelles et constatation par arrêté interministériel |
| Q17 | Accident survenu au Maroc, suis-je assuré ? | 3, L211-4 | 19 | R211-8 — Dommages non couverts par l'obligation d'assurance (conducteur, biens transportés) |
| Q25 | Dans quel délai l'assuré peut-il agir en justice contre son assureur ? | L114-1 | 10 | L211-12 — Procédures d'indemnisation |
| Q27 | La victime peut-elle réclamer directement l'indemnisation à l'assureur du responsable ? | L124-3 | 2 | A211-11-annexe — Procédures d'indemnisation |

## Tableau croisé — Par article

Requêtes pas en 1re position, selon le ou les retrievers qui les ratent.

| Ratée par | Nb | Requêtes |
|---|---|---|
| BM25 (stem) seulement | 5 | Q02, Q05, Q10, Q19, Q30 |
| Dense (bge-m3) seulement | 5 | Q08, Q13, Q16, Q18, Q23 |
| Hybride (RRF) seulement | 0 | — |
| Les trois | 4 | Q04, Q11, Q25, Q27 |
