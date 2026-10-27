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

### Comparaison avec et sans reformulation

Même modèle (`gemini-3.5-flash-lite`, `reasoning_effort: minimal`), mêmes intakes, même retrieval. Avec
reformulation : lancement du 21 octobre 2026 à 18 h 03 (ce rapport). Sans reformulation : lancement du même jour à
18 h 47 (`results/eval_policy_agent_sans_reformulation.md`). Un seul lancement chacun, à température 0.

| Métrique | Avec reformulation | Sans reformulation |
|---|---|---|
| Verdicts corrects | 7 / 10 | 7 / 10, dont 1 par hasard (D03, réponse P4 invalide) |
| Rappel complet | 62 % | 67 % |
| Rappel périmètre couverture | 83 % | 83 % |
| Précision | 58 % | 67 % |
| Rappel des articles fournis | 70 % | 75 % |
| Durée moyenne par dossier | non mesurée (durées ajoutées au script après ce lancement) | 11,9 s, dont 2,2 s d'appel Gemini |
| Appels Gemini | 20 (2 par dossier) | 10 (1 par dossier) |

La durée sans reformulation comprend l'attente d'au moins 13 s imposée entre deux appels pour respecter la limite
de l'offre gratuite ; avec reformulation, cette attente s'ajoute une fois de plus par dossier.

**Dossiers dont le verdict change** :
- **D06** (vol) : « couvert » → « indetermine », verdict correct sans reformulation. Sans reformulation, l'article 18
  (pièces à fournir) fait partie des articles fournis, et la justification relève que « le dossier ne précise pas si
  un dépôt de plainte a été effectué ni si des traces matérielles d'effraction ont été constatées » (articles 9 et 18).
  C'est exactement la réserve qui manquait avec reformulation.
- **D08** (bris de glace) : « couvert » → « partiel », verdict incorrect sans reformulation. Les articles attendus (8,
  20) sont fournis et cités dans les deux cas ; le modèle classe en « partiel » une franchise de 80 €, qui ne réduit
  pas « nettement » l'indemnisation au sens du prompt. C'est une variation du raisonnement, pas du retrieval.
- **D03** : « indetermine » dans les deux cas, mais sans reformulation la réponse P4 était un JSON invalide : le
  verdict « indetermine » vient du code, pas d'une analyse.

**Articles fournis** : ils changent pour les 10 dossiers (1 à 4 articles sur 10 remplacés), mais les articles
attendus fournis ne changent que pour D06 (+ 18). Les autres remplacements portent sur des articles non attendus,
pas toujours anodins : sans reformulation, L113-8 (nullité pour fausse déclaration intentionnelle) n'est plus
fourni pour D02 ni D07, et l'article 16 (conducteur non désigné) ou 23 (fraude) apparaissent dans plusieurs dossiers.

**La reformulation justifie-t-elle son appel supplémentaire ?** Pas sur ce jeu de test. Elle double le nombre
d'appels Gemini (donc la consommation du quota) sans gain mesurable : mêmes verdicts corrects une fois D03 mis à
part, et des écarts de rappel et de précision d'un dossier, dans le bruit à 10 dossiers. Ce résultat s'explique :
les sous-questions sont générées par des modèles de phrase déjà rédigés dans le vocabulaire du contrat, alors que
la reformulation a été conçue pour des questions en langage courant (synonymes et connaissance manquante de
l'évaluation du retrieval : Q09, Q11, Q17, Q25). Elle reste à évaluer sur des questions libres, ou avec la vraie
sortie de P1. En attendant, `--sans-reformulation` (ou `reformulation=False`) est le réglage le plus économe, sans
perte observée.

### Réglages v2.1 et stabilité (21 octobre 2026)

Code v2.1 : reformulation désactivée par défaut, température 0, sortie structurée pour P4 (`response_format`
`json_schema` avec le schéma de P4). Même modèle (`gemini-3.5-flash-lite`, `reasoning_effort: minimal`). Deux
lancements de suite avec `--sans-cache` : `results/eval_policy_agent_v2_1_l1.md` et `_v2_1_l2.md`.

| Métrique | 18 h 03 (avec reformulation) | Sans reformulation (18 h 47) | v2.1, lancement 1 | v2.1, lancement 2 |
|---|---|---|---|---|
| Verdicts corrects | 7 / 10 | 7 / 10 (dont D03 par hasard) | 7 / 10 | 6 / 10 |
| Réponses P4 invalides | 0 | 1 (D03) | 0 | 0 |
| Rappel complet | 62 % | 67 % | 67 % | 57 % |
| Rappel périmètre couverture | 83 % | 83 % | 83 % | 71 % |
| Précision | 58 % | 67 % | 53 % | 57 % |
| Rappel des articles fournis | 70 % | 75 % | 75 % | 75 % |
| Durée moyenne d'appel Gemini | non mesurée | 2,1 s | 4,3 s (D09 : 22,3 s) | 2,0 s |
| Appels Gemini | 20 | 10 | 10 | 10 |

| Dossier | Attendu | 18 h 03 | Sans reformulation | v2.1, lancement 1 | v2.1, lancement 2 |
|---|---|---|---|---|---|
| D01 | accept | couvert | couvert | couvert | couvert |
| D02 | reject | non_couvert | non_couvert | non_couvert | non_couvert |
| D03 | investigate | indetermine | indetermine (JSON invalide) | **couvert** | indetermine |
| D04 | investigate | couvert | couvert | couvert | couvert |
| D05 | investigate | couvert | couvert | couvert | couvert |
| D06 | investigate | couvert | indetermine | indetermine | indetermine |
| D07 | investigate | partiel | partiel | partiel | partiel |
| D08 | accept | couvert | **partiel** | couvert | **partiel** |
| D09 | investigate | indetermine | indetermine | indetermine | **couvert** |
| D10 | accept | couvert | couvert | couvert | couvert |

**Stabilité : les verdicts ne sont pas identiques entre les deux lancements v2.1.** 3 dossiers sur 10 changent
(D03, D08, D09), alors que la température est à 0 et que les articles fournis sont identiques pour les 10 dossiers
entre les deux lancements : la variation vient du modèle, pas du retrieval. Les articles cités varient aussi (D10 :
8, 20 et A121-1-annexe-7 au lancement 1, 8 seul au lancement 2). Les dossiers instables sont les cas limites :
D03 (responsabilité non établie sans constat), D08 (une franchise de 80 € rend-elle la couverture « partielle » ?),
D09 (déclaration de tentative de vol au-delà de 2 jours ouvrés). Des 7 autres dossiers, 6 ont le même verdict dans
les quatre lancements (D01, D02, D04, D05, D07, D10) ; D06 est « indetermine » dans les trois lancements sans
reformulation, mais était « couvert » à 18 h 03, avec reformulation.

Conséquences :
- un écart d'un dossier entre deux configurations (par exemple 7 / 10 contre 6 / 10) est du même ordre que la
  variation d'un lancement à l'autre de la même configuration : il ne permet pas de conclure. Comparer des
  configurations demande plusieurs lancements chacune, ou un jeu de dossiers plus grand ;
- la sortie structurée a supprimé les réponses invalides sur ces 20 appels (0 contre 1 sur les 10 précédents), sans
  coût de durée visible ; c'est cohérent avec son objectif, mais 20 appels ne suffisent pas à le démontrer ;
- pour la production, les cas limites (D08 : seuil de « partiel ») gagneraient à être tranchés par une règle dans le
  prompt ou dans le code plutôt que laissés à l'appréciation du modèle.

### Modèles locaux avec Ollama : qwen2.5:3b et qwen2.5:7b (27 octobre 2026)

Même code v2.1 (sans reformulation, température 0, sortie structurée `json_schema`), mêmes intakes, même retrieval
(articles fournis identiques pour les trois modèles), seul le LLM de P4 change : `LLM_PROVIDER=ollama`, endpoint
`/v1` compatible OpenAI, sans reasoning_effort. Un lancement chacun avec `--sans-cache` :
`results/eval_policy_agent_ollama_3b.md` et `_ollama_7b.md`. Machine : Ollama 0.40.11, NVIDIA GeForce RTX 4050
Laptop (6 Go), modèles chargés à 100 % sur le GPU. qwen2.5:3b est le modèle du `.env.example` de la branche ines.
Pour Gemini, les deux lancements v2.1 ci-dessus (même code).

| Métrique | gemini-3.5-flash-lite (v2.1, lancement 1 / 2) | qwen2.5:3b | qwen2.5:7b |
|---|---|---|---|
| Verdicts corrects | 7 / 10 ; 6 / 10 | 4 / 10, dont 3 pour une mauvaise raison | 6 / 10, dont 1 pour une mauvaise raison |
| Verdicts « non_couvert » à tort (rejet automatique) | 0 ; 0 | **5** (D01, D03, D05, D06, D10) | 0 |
| Rappel périmètre couverture | 83 % ; 71 % | 42 % | 77 % |
| Précision | 53 % ; 57 % | 24 % | 60 % |
| Rappel complet | 67 % ; 57 % | 38 % | 57 % |
| Réponses P4 invalides | 0 ; 0 | 0 | 0 |
| Durée moyenne par dossier | 13,9 s ; 12,8 s | 11,5 s | 16,2 s |
| dont appel au LLM | 4,3 s ; 2,0 s | 9,7 s | 14,0 s |

Pour Gemini, la durée par dossier comprend surtout l'attente d'au moins 13 s imposée entre deux appels (offre
gratuite) ; l'appel lui-même dure environ 2 s (D09 : 22,3 s au lancement 1). Avec Ollama, il n'y a pas d'attente
imposée : la durée par dossier est le retrieval plus l'appel local.

| Dossier | Attendu | Gemini, lancement 1 | Gemini, lancement 2 | qwen2.5:3b | qwen2.5:7b |
|---|---|---|---|---|---|
| D01 | accept | couvert | couvert | **non_couvert** | couvert |
| D02 | reject | non_couvert | non_couvert | non_couvert (15 non cité) | non_couvert |
| D03 | investigate | **couvert** | indetermine | **non_couvert** | partiel |
| D04 | investigate | couvert | couvert | partiel | couvert |
| D05 | investigate | couvert | couvert | **non_couvert** | couvert |
| D06 | investigate | indetermine | indetermine | **non_couvert** | couvert |
| D07 | investigate | partiel | partiel | partiel | partiel |
| D08 | accept | couvert | **partiel** | **partiel** | couvert |
| D09 | investigate | indetermine | **couvert** | indetermine (forcé par le code) | **couvert** |
| D10 | accept | couvert | couvert | **non_couvert** | couvert |

**qwen2.5:3b invente des exclusions.** Dans 7 dossiers sur 10, sa justification applique l'exclusion de l'article
15 (« usage non déclaré, transport onéreux de personnes ») : D03, D04, D05, D06, D08, D09 et D10. Seul D02 (course
VTC) contient ce fait, et c'est justement le dossier où il ne l'invoque pas : le modèle reprend le texte de
l'article fourni comme s'il décrivait le dossier. D01 et D02 sont refusés pour un permis non valide ou une
alcoolémie (article 14) que les dossiers ne mentionnent pas. Ses verdicts corrects ne sont donc pas fiables : D02
est « non_couvert » pour ce motif inventé, sans citer l'article 15 ; D04 est « partiel » à cause de l'exclusion
d'usage inventée ; D09 est « indetermine » parce que la réponse ne citait aucun article fourni et que le contrôle du
code a ramené le verdict à « indetermine » (la justification concluait « non couvert »). D07 (« partiel ») mêle la
bonne franchise à une « exclusion pour les accidents de route » (R211-10) qui n'existe pas. Avec l'adaptateur `rag/integration.py`, « non_couvert » devient `excluded`,
que le `decision_agent` de la branche ines transforme en REJECT : 5 sinistres couverts seraient refusés
automatiquement.

**qwen2.5:7b raisonne correctement mais sans réserve.** Aucun refus à tort, les articles cités sont ceux attendus
pour la couverture (6 ou 8 ou 9, et 20), D02 et D07 sont justifiés comme avec Gemini. Ses deux écarts par rapport à
Gemini vont dans le même sens : il répond « couvert » dès qu'une garantie souscrite correspond, sans relever les
conditions à vérifier (D06 : plainte et traces d'effraction de l'article 9 ; D09 : déclaration de vol au-delà de
2 jours ouvrés, article 17). Gemini relève la première dans ses deux lancements et la seconde dans un sur deux. D03
est « partiel » pour une mauvaise raison (usage non déclaré, que rien dans le dossier n'établit), ce qui donne quand
même l'investigation attendue. D04 et D05 sont « couvert », comme avec Gemini, pour la raison expliquée plus haut :
les anomalies sont dans les pièces, que le Policy Agent ne voit pas.

**JSON** : aucune réponse invalide sur les 20 appels Ollama. La sortie structurée est bien appliquée par Ollama (le
schéma passe dans son paramètre `format`), même pour le modèle 3b.

**Contexte d'Ollama** : le serveur a chargé les modèles avec une fenêtre de 4 096 tokens (valeur par défaut). Les
prompts P4 de ce jeu de test font de 3 000 à 3 700 tokens et le journal d'Ollama n'indique aucune troncature, mais le
plus long appel a utilisé 3 981 tokens sur 4 096 (prompt et réponse). Le code autorise jusqu'à ~6 000 tokens
(`MAX_PROMPT_TOKENS`) : au-delà de 4 096, Ollama tronquerait le prompt sans erreur. En production, régler
`OLLAMA_CONTEXT_LENGTH=8192` sur le serveur Ollama.

Limites : un seul lancement par modèle local (la variation entre deux lancements Gemini était de 3 dossiers sur
10), 10 dossiers, un seul GPU. Les écarts de 1 dossier entre Gemini et qwen2.5:7b ne permettent pas de conclure ;
l'écart avec qwen2.5:3b (5 refus à tort, exclusions inventées) est d'une autre nature et se lit dans les
justifications, pas seulement dans les scores.

**Recommandation pour l'équipe** :
- **Ne pas utiliser qwen2.5:3b pour le Policy Agent**, bien qu'il soit le modèle par défaut du `.env.example` :
  il invente des exclusions et produirait des refus automatiques injustifiés. Il peut rester pour d'autres agents
  si leurs évaluations le permettent.
- **En local (Ollama), utiliser `OLLAMA_POLICY_MODEL=qwen2.5:7b`**, avec `OLLAMA_CONTEXT_LENGTH=8192`. Ses
  résultats sont proches de ceux de Gemini sur ce jeu de test (6 / 10, aucun refus à tort, précision 60 %), pour
  ~14 s par appel sur un GPU portable de 6 Go. Sa faiblesse, l'absence de réserves (D06, D09), compte dans
  l'architecture de la branche ines : « covered » sans fraude devient un ACCEPT automatique.
- **Gemini (`gemini-3.5-flash-lite`) reste le meilleur choix quand un appel externe est acceptable** : réserves
  mieux relevées, appel de ~2 s, mais quota de l'offre gratuite (13 s entre deux appels) et données du dossier
  envoyées à un service externe.
