# Évaluation de bout en bout du Policy Agent

- Date : 2026-10-27 12:13 ; fournisseur : ollama ; modèle : `qwen2.5:3b` ; reasoning_effort : `non envoyé` ; reformulation : non.
- Dossiers évalués : 10 sur 10.
- Intake : construit par `intake_depuis_dossier` (résumés courts rédigés à la main au format P1, en attendant la vraie sortie de P1) ; conditions particulières : `contrat_reference`.
- Verdict attendu : accept → couvert ; reject → non_couvert ; investigate → partiel ou indetermine.
- « Périmètre couverture » : rappel sans les articles 18, 19, 23, 24, 25, 26 (pièces, expertise, fraude, procédures internes), que les sous-questions de couverture ne visent pas ; ils relèvent des agents Fraud et Decision.

## Résultats par dossier

| Dossier | Attendu | Verdict | Verdict OK | Articles attendus | Fournis | Cités | Rappel (complet) | Rappel (périmètre couverture) | Précision | Rappel fournis | Confiance | Appels (cache / réseau) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D01 | accept | non_couvert | **non** | 20, 21, 6 | **20**, 16, 7, **21**, 17, **6**, R211-10, 14, R421-18, 22 | 6, 14, 20 | 67 % | 67 % | 67 % | 100 % | haute | 0 / 1 |
| D02 | reject | non_couvert | oui | 15 | 7, 20, A121-1-annexe-7, **15**, L113-9, 17, 6, 23, 14, 22 | 6, 20 | 0 % | 0 % | 0 % | 100 % | moyenne | 0 / 1 |
| D03 | investigate | non_couvert | **non** | 17, 25 | 20, 7, 16, 21, **17**, 6, 15, R421-18, 22, R211-10 | 6, 15, 20 | 0 % | 0 % | 0 % | 50 % | haute | 0 / 1 |
| D04 | investigate | partiel | oui | 19, 25 | 20, 16, 7, 6, 21, 17, R211-10, 15, R421-18, 22 | 6, 15, 20 | 0 % | — | 0 % | 0 % | haute | 0 / 1 |
| D05 | investigate | non_couvert | **non** | 19, 23, 25 | 20, 16, 7, 21, R421-18, 17, 6, 15, 22, R211-10 | 6, 15, 20 | 0 % | — | 0 % | 0 % | haute | 0 / 1 |
| D06 | investigate | non_couvert | **non** | 18, 9 | **9**, R421-18, A121-1-annexe-7, 22, 20, 17, 16, 15, R421-2, **18** | 15, 20, 18 | 50 % | 0 % | 33 % | 100 % | moyenne | 0 / 1 |
| D07 | investigate | partiel | oui | 16, 20, 6 | **16**, R211-10, **6**, L113-9, 23, 2, 7, **20**, 17, 22 | 6, 20, 17, 22, R211-10 | 67 % | 67 % | 40 % | 100 % | haute | 0 / 1 |
| D08 | accept | partiel | **non** | 20, 8 | **8**, A121-1-annexe-7, **20**, 17, 7, L121-18, L421-9, L421-12, 15, L113-2 | 8, 15, 20, L113-2 | 100 % | 100 % | 50 % | 100 % | haute | 0 / 1 |
| D09 | investigate | indetermine | oui | 17, 9 | **9**, A121-1-annexe-7, 20, **17**, 15, 16, 22, R421-2, L211-1, 8 | — | 0 % | 0 % | — | 100 % | basse | 0 / 1 |
| D10 | accept | non_couvert | **non** | 20, 8 | **8**, **20**, A121-1-annexe-7, 17, 7, L121-18, L421-9, R211-10, 15, L113-2 | 8, 20, 17, 15, A121-1-annexe-7, L121-18, L421-9, R211-10, L113-2 | 100 % | 100 % | 22 % | 100 % | basse | 0 / 1 |

Dans la colonne « Fournis », les articles attendus sont en gras.

## Moyennes

Sur les 10 dossiers avec une réponse P4 (0 erreur(s) d'appel exclue(s), sauf pour le rappel des articles fournis, mesuré avant l'appel P4).

| Métrique | Valeur |
|---|---|
| Verdict cohérent | 4 / 10 |
| Rappel des articles cités, complet | 38 % |
| Rappel des articles cités, périmètre couverture | 42 % |
| Précision des articles (dossiers avec au moins un article cité) | 24 % |
| Rappel des articles fournis au LLM | 75 % |

Le rappel **complet** compte tous les articles attendus du dossier ; le rappel **périmètre couverture** ne compte que ceux qui relèvent de l'analyse de couverture, sans les articles 18, 19, 23, 24, 25 et 26 (pièces, expertise, fraude, procédures internes), qui relèvent des agents Fraud et Decision. Un écart entre les deux vient de ces articles hors périmètre, pas d'une erreur du Policy Agent. Un dossier dont tous les articles attendus sont hors périmètre n'a pas de rappel périmètre (« — ») et n'entre pas dans sa moyenne.

## Échecs et cause

- **D01** (Sinistre simple, accepté) :
  - article 21 fourni mais non cité : raisonnement
  - verdict « non_couvert » au lieu de couvert : raisonnement
  - cités sans être attendus : 14
- **D02** (Exclusion applicable : usage VTC non déclaré) :
  - article 15 fourni mais non cité : raisonnement
  - cités sans être attendus : 6, 20
- **D03** (Incohérence de dates déclaration / constat) :
  - article 17 fourni mais non cité : raisonnement
  - article 25 absent des articles fournis : retrieval (hors périmètre couverture)
  - verdict « non_couvert » au lieu de indetermine ou partiel : raisonnement
  - cités sans être attendus : 6, 15, 20
- **D04** (Photos contredisant le récit (choc frontal déclaré, dommages arrière)) :
  - article 19 absent des articles fournis : retrieval (hors périmètre couverture)
  - article 25 absent des articles fournis : retrieval (hors périmètre couverture)
  - cités sans être attendus : 6, 15, 20
- **D05** (Facture au montant gonflé) :
  - article 19 absent des articles fournis : retrieval (hors périmètre couverture)
  - article 23 absent des articles fournis : retrieval (hors périmètre couverture)
  - article 25 absent des articles fournis : retrieval (hors périmètre couverture)
  - verdict « non_couvert » au lieu de indetermine ou partiel : raisonnement
  - cités sans être attendus : 6, 15, 20
- **D06** (Pièce manquante ou illisible) :
  - article 9 fourni mais non cité : raisonnement
  - verdict « non_couvert » au lieu de indetermine ou partiel : raisonnement
  - cités sans être attendus : 15, 20
- **D07** (Garantie ambiguë : sortie de route, conducteur non désigné) :
  - article 16 fourni mais non cité : raisonnement
  - cités sans être attendus : 17, 22, R211-10
- **D08** (Dossier avec déclaration audio) :
  - verdict « partiel » au lieu de couvert : raisonnement
  - cités sans être attendus : 15, L113-2
- **D09** (Déclaration hors délai (vol déclaré après 6 jours)) :
  - article 17 fourni mais non cité : raisonnement
  - article 9 fourni mais non cité : raisonnement
- **D10** (Bris de glace simple, réparation d'impact) :
  - verdict « non_couvert » au lieu de couvert : raisonnement
  - cités sans être attendus : 17, 15, A121-1-annexe-7, L121-18, L421-9, R211-10, L113-2

Avec 10 dossiers, un dossier représente 10 % du verdict : ces chiffres décrivent ce jeu de test, pas une performance générale.
