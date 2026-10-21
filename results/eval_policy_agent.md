# Évaluation de bout en bout du Policy Agent

- Date : 2026-10-21 18:03 ; modèle : `gemini-3.5-flash-lite` ; reasoning_effort : `minimal` ; reformulation : oui.
- Dossiers évalués : 10 sur 10.
- Intake : construit par `intake_depuis_dossier` (résumés courts rédigés à la main au format P1, en attendant la vraie sortie de P1) ; conditions particulières : `contrat_reference`.
- Verdict attendu : accept → couvert ; reject → non_couvert ; investigate → partiel ou indetermine.
- « Périmètre couverture » : rappel sans les articles 18, 19, 23, 24, 25, 26 (pièces, expertise, fraude, procédures internes), que les sous-questions de couverture ne visent pas ; ils relèvent des agents Fraud et Decision.

## Résultats par dossier

| Dossier | Attendu | Verdict | Verdict OK | Articles attendus | Fournis | Cités | Rappel (complet) | Rappel (périmètre couverture) | Précision | Rappel fournis | Confiance | Appels (cache / réseau) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D01 | accept | couvert | oui | 20, 21, 6 | **20**, 7, **21**, 17, **6**, R211-10, D125-5-9, 14, 15, A125-6 | 6, 20 | 67 % | 67 % | 100 % | 100 % | haute | 2 / 0 |
| D02 | reject | non_couvert | oui | 15 | 7, 20, A121-1-annexe-7, **15**, 6, L113-9, 17, R211-10, L113-8, 14 | 15 | 100 % | 100 % | 100 % | 100 % | haute | 2 / 0 |
| D03 | investigate | indetermine | oui | 17, 25 | 20, 7, 21, **17**, 15, 6, D125-5-9, R211-10, A125-6, 22 | 6, 20, 21 | 0 % | 0 % | 0 % | 50 % | haute | 0 / 2 |
| D04 | investigate | couvert | **non** | 19, 25 | 20, 7, 6, 21, 17, R211-10, R421-20, 15, 22, A125-6 | 6, 20 | 0 % | — | 0 % | 0 % | haute | 0 / 2 |
| D05 | investigate | couvert | **non** | 19, 23, 25 | 7, 20, 21, R421-18, 17, A121-1-annexe-7, 6, L211-4, 15, R211-10 | 6, 20 | 0 % | — | 0 % | 0 % | haute | 0 / 2 |
| D06 | investigate | couvert | **non** | 18, 9 | **9**, R421-18, 22, A121-1-annexe-7, 20, 17, 15, R211-10, 16, A125-6-4-2 | 9, 20 | 50 % | 100 % | 50 % | 50 % | haute | 0 / 2 |
| D07 | investigate | partiel | oui | 16, 20, 6 | **16**, R211-10, **20**, **6**, L113-9, 7, 14, 17, L113-8, A125-6-4 | 6, 16, 20 | 100 % | 100 % | 100 % | 100 % | haute | 0 / 2 |
| D08 | accept | couvert | oui | 20, 8 | **8**, A121-1-annexe-7, **20**, 7, 17, R211-11, L125-2, L121-18, R421-4, A125-6-4-2 | 8, 20 | 100 % | 100 % | 100 % | 100 % | haute | 0 / 2 |
| D09 | investigate | indetermine | oui | 17, 9 | **9**, A121-1-annexe-7, 20, **17**, 15, 7, 22, 16, A125-6-4, 8 | 9, 17, 20 | 100 % | 100 % | 67 % | 100 % | haute | 0 / 2 |
| D10 | accept | couvert | oui | 20, 8 | **8**, **20**, A121-1-annexe-7, 17, 7, R211-10, 15, L113-2, A125-6-4, L121-18 | 8, 20, A121-1-annexe-7 | 100 % | 100 % | 67 % | 100 % | haute | 0 / 2 |

Dans la colonne « Fournis », les articles attendus sont en gras.

## Moyennes

Sur les 10 dossiers avec une réponse P4 (0 erreur(s) d'appel exclue(s), sauf pour le rappel des articles fournis, mesuré avant l'appel P4).

| Métrique | Valeur |
|---|---|
| Verdict cohérent | 7 / 10 |
| Rappel des articles cités, complet | 62 % |
| Rappel des articles cités, périmètre couverture | 83 % |
| Précision des articles (dossiers avec au moins un article cité) | 58 % |
| Rappel des articles fournis au LLM | 70 % |

Le rappel **complet** compte tous les articles attendus du dossier ; le rappel **périmètre couverture** ne compte que ceux qui relèvent de l'analyse de couverture, sans les articles 18, 19, 23, 24, 25 et 26 (pièces, expertise, fraude, procédures internes), qui relèvent des agents Fraud et Decision. Un écart entre les deux vient de ces articles hors périmètre, pas d'une erreur du Policy Agent. Un dossier dont tous les articles attendus sont hors périmètre n'a pas de rappel périmètre (« — ») et n'entre pas dans sa moyenne.

## Échecs et cause

- **D01** (Sinistre simple, accepté) :
  - article 21 fourni mais non cité : raisonnement
- **D03** (Incohérence de dates déclaration / constat) :
  - article 17 fourni mais non cité : raisonnement
  - article 25 absent des articles fournis : retrieval (hors périmètre couverture)
  - cités sans être attendus : 6, 20, 21
- **D04** (Photos contredisant le récit (choc frontal déclaré, dommages arrière)) :
  - article 19 absent des articles fournis : retrieval (hors périmètre couverture)
  - article 25 absent des articles fournis : retrieval (hors périmètre couverture)
  - verdict « couvert » au lieu de indetermine ou partiel : raisonnement
  - cités sans être attendus : 6, 20
- **D05** (Facture au montant gonflé) :
  - article 19 absent des articles fournis : retrieval (hors périmètre couverture)
  - article 23 absent des articles fournis : retrieval (hors périmètre couverture)
  - article 25 absent des articles fournis : retrieval (hors périmètre couverture)
  - verdict « couvert » au lieu de indetermine ou partiel : raisonnement
  - cités sans être attendus : 6, 20
- **D06** (Pièce manquante ou illisible) :
  - article 18 absent des articles fournis : retrieval (hors périmètre couverture)
  - verdict « couvert » au lieu de indetermine ou partiel : raisonnement
  - cités sans être attendus : 20

Avec 10 dossiers, un dossier représente 10 % du verdict : ces chiffres décrivent ce jeu de test, pas une performance générale.

## Analyse

**Conditions** : `gemini-3.5-flash-lite`, `reasoning_effort: minimal`, reformulation active, température 0, un seul
lancement. Les intakes sont **simulés** : les circonstances sont des résumés rédigés à la main au format P1
(`INTAKE_TEST` dans `rag/policy_agent.py`), pas la sortie réelle de P1. Les conditions particulières viennent de
`contrat_reference`. La vérité terrain (`attendu`) n'a pas été modifiée.

### D04, D05, D06 : couverts par le contrat, investigation demandée par les pièces

Les trois dossiers relèvent d'une garantie souscrite (dommages tous accidents pour D04 et D05, vol pour D06), et le
Policy Agent répond « couvert ». L'investigation attendue vient d'anomalies **entre les pièces** :

- D04 : photos qui contredisent le récit (choc frontal déclaré, dommages à l'arrière) ;
- D05 : facture très supérieure aux dommages visibles, constat absent malgré un tiers identifié ;
- D06 : récépissé de plainte manquant.

Le Policy Agent ne reçoit que l'intake et les conditions particulières : ni les photos, ni la facture, ni la liste
des pièces. Seuls les agents Vision, Document et Fraud peuvent détecter ces anomalies, et c'est au Decision Agent
de combiner leur avis avec la couverture. Ces trois « échecs » de verdict ne sont donc pas des erreurs d'analyse de
couverture : ils illustrent pourquoi une architecture multi-agents est nécessaire, une seule analyse de couverture
ne pouvant pas conclure à l'investigation. Ils pèsent aussi sur le score « verdict cohérent » (7 / 10), parce que la
correspondance investigate ↔ partiel ou indetermine compare une décision de traitement à un verdict de couverture.

### D06 : « couvert » sans réserve

L'article 9 du contrat exige que le vol soit « établi par des traces matérielles d'effraction du véhicule ou de
forcement de la direction ou des organes de démarrage » et que l'assuré dépose plainte et en remette la copie.
La justification de l'agent (« le véhicule a été volé devant le domicile de l'assuré, ce qui active la garantie vol
prévue à l'article 9 ») ne mentionne aucune de ces deux conditions. Le dossier ne liste pas les pièces fournies,
l'agent ne pouvait donc pas savoir si elles manquaient ; il aurait dû signaler qu'elles restent à vérifier.
Limite à corriger en v3 avec le champ `points_a_verifier`, par exemple : « couvert sous réserve du récépissé de
plainte et de traces d'effraction (article 9) ».

### D10 : citation pertinente non prévue par la vérité terrain

L'agent cite A121-1-annexe-7 (clause type bonus-malus, article 7) : « le sinistre mettant en jeu uniquement l'une
des garanties suivantes : vol, incendie, bris de glace, n'entraîne pas l'application de la majoration ». C'est
exact pour un bris de glace seul : pas de malus. La vérité terrain ne prévoit pas cet article, ce qui fait baisser
la précision de D10 à 67 % alors que la citation est juste.

### Précision sous-estimée

Pour les dossiers « investigate », la vérité terrain liste les articles de la **décision finale** (17 et 25 pour
D03, 19 et 25 pour D04, 19, 23 et 25 pour D05, 18 et 9 pour D06) : fraude, expertise, critères d'investigation,
pièces. Elle ne liste pas les articles de la **couverture**. Or l'agent cite, à juste titre pour son rôle, la
garantie et les franchises (6 et 20 pour D03, D04 et D05), ce qui donne une précision de 0 % sur ces trois
dossiers. Avec D10 (citation exacte non prévue), la précision moyenne de 58 % est donc une borne basse : sur les
quatre dossiers « accept » et « reject » (D01, D02, D08, D10), dont la vérité terrain porte sur la couverture,
elle est de 92 %. Une vérité terrain séparée pour la couverture (articles attendus du Policy Agent) rendrait la
mesure plus juste.

### Autres points

- La reformulation R1 a introduit une notion hors sujet pour D02 (question 4, délai) : « notifier l'événement de
  mer ou l'accident automobile » (vocabulaire de l'assurance maritime, exclue du corpus). Le verdict de D02 n'en est
  pas affecté (« non_couvert », article 15 cité), mais la recherche correspondante est bruitée.
- Avec 10 dossiers, un dossier vaut 10 % du score de verdict : ces chiffres décrivent ce jeu de test, pas une
  performance générale.
