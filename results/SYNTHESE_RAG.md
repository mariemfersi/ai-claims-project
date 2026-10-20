# Synthèse des expériences de retrieval (RAG)

Partie RAG de l'agent de gestion de sinistres auto. Toutes les expériences ont été faites
le 20 octobre 2026 avec `rag/eval_retrieval.py`, sur 32 requêtes de test (`rag/test_queries.json`).

**Configuration retenue : chunking « Par article » + hybride RRF + BM25 racinisé (`--bm25-stem`) + dense `BAAI/bge-m3`**,
avec MRR@5 = 0.79 et hit@5 = 0.91 (section 4).

Métriques utilisées :
- **hit@k** : part des requêtes dont au moins un article attendu figure dans les k premiers chunks.
- **MRR@5** : moyenne de 1/rang du premier bon chunk, avec 0 s'il n'est pas dans le top 5.
- **Tokens top-5** : nombre moyen de tokens (`cl100k`) des 5 chunks envoyés au LLM.

Avec 32 requêtes, **une requête vaut environ 0,03** sur hit@k (voir section 5).

Sources des chiffres :
- `results/retrieval_eval_*.md` et `.json` ;
- `results/erreurs_retrieval_*.md` ;
- le commentaire en tête de `rag/eval_retrieval.py` ;
- `git log`.

Les seuls chiffres qui ne figurent pas dans ces fichiers sont ceux de la mesure de troncature (section 2.e). Elle a été faite ponctuellement et son script n'est pas versionné.

---

## 1. Corpus

| Document | Fichier | Articles | Source |
|---|---|---|---|
| Contrat (conditions générales auto, fictif) | `data/corpus/conditions_generales_auto.md` | 26 (articles 1 à 26) | `contrat` |
| Code des assurances, extraits liés à l'auto | `data/corpus/code_assurances_extraits.md` | 428, dont 244 `lien_auto: direct` et 184 `lien_auto: indirect` | `code_assurances` |

> **Écart à corriger** : le message du commit 7ac528c annonce 415 articles, mais le fichier en contient
> 428, dont 17 annexes, sans doublon d'identifiant. Les chiffres de cette synthèse sont ceux du fichier.

**Règle de sélection** des articles du Code (en-tête du fichier ; texte Légifrance, dernière modification le 20 août 2026) :
- **`lien_auto: direct`** :
  - assurance des véhicules terrestres à moteur (Livre II, Titre Ier) ;
  - bureau central de tarification, FGAO, organisme d'indemnisation, organisme d'information ;
  - clause type bonus-malus.
- **`lien_auto: indirect`** : règles générales qui s'appliquent à tout contrat auto :
  - règles communes du contrat (Livre Ier, Titre Ier) ;
  - assurances de dommages, incendie et tempête, responsabilité ;
  - catastrophes naturelles et technologiques, attentats ;
  - protection juridique, loi applicable ;
  - fonds de garantie en cas de défaillance d'un assureur.
- **Exclus** :
  - assurance vie et de personnes, groupe, capitalisation, maritime et aérien, Alsace-Moselle ;
  - autres assurances obligatoires (construction, médicale, chasse, habitation, remontées mécaniques) ;
  - entreprises (Livre III), distribution (Livre V) ;
  - dans les chapitres retenus, les sections sans lien avec l'auto (chasse, relogement, dommages miniers,
    construction, commissions administratives).

**Nombre de chunks** (les deux fichiers sont découpés séparément) :

| Chunking | Chunks | Détail |
|---|---|---|
| Taille fixe 500/50 (fenêtres de 500 tokens, 50 de chevauchement) | 305 | — |
| Par article (un chunk par article, articles de plus de 450 tokens découpés aux alinéas) | 594 | 26 pour le contrat + 568 pour le Code (222 chunks sont des parties d'articles longs) |
| Par article avec `--filtre direct` | 339 | contrat + articles `direct` |

---

## 2. Expériences, dans l'ordre

### a. Chunking taille fixe ou par article (BM25, dense e5-small)

**Testé** : les deux chunkings avec BM25 et avec le dense `intfloat/multilingual-e5-small`
(source : `retrieval_eval_tout_multilingual-e5-small.md`).

| Configuration | Chunks | hit@1 | hit@3 | hit@5 | MRR@5 | Tokens top-5 |
|---|---|---|---|---|---|---|
| Taille fixe + BM25 | 305 | 0.41 | 0.62 | 0.72 | 0.51 | 2491 |
| Taille fixe + Dense e5 | 305 | 0.31 | 0.53 | 0.56 | 0.41 | 2491 |
| Par article + BM25 | 594 | 0.56 | 0.78 | 0.81 | 0.67 | 1360 |
| Par article + Dense e5 | 594 | 0.59 | 0.75 | 0.78 | 0.67 | 1140 |

Le chunking par article est meilleur sur toutes les métriques et envoie environ deux fois moins de tokens au LLM.
Ce résultat est même prudent : une fenêtre de taille fixe compte comme un succès pour chaque article qu'elle
recouvre, même partiellement, ce qui la favorise.

**Décision** : chunking « Par article ».

### b. Recherche hybride (Reciprocal Rank Fusion)

**Testé** : fusion des classements BM25 et dense, score = 1/(60 + rang_BM25) + 1/(60 + rang_dense).
Les embeddings ne sont calculés qu'une fois par chunking (source : `retrieval_eval_tout_multilingual-e5-small.md`).

| Configuration | hit@1 | hit@3 | hit@5 | MRR@5 | Tokens top-5 |
|---|---|---|---|---|---|
| Taille fixe + Hybride | 0.50 | 0.66 | 0.72 | 0.59 | 2491 |
| Par article + BM25 | 0.56 | 0.78 | 0.81 | 0.67 | 1360 |
| Par article + Dense e5 | 0.59 | 0.75 | 0.78 | 0.67 | 1140 |
| Par article + Hybride | 0.59 | 0.78 | 0.78 | 0.68 | 1341 |

- **Taille fixe** : l'hybride apporte un gain net.
- **Par article** : sans racinisation, le gain est faible et le hit@5 baisse d'une requête par rapport à BM25.
- **Erreurs** : dans l'analyse d'erreurs, l'hybride ne rate aucune requête que BM25 et le dense réussissent tous les deux.

**Décision** : hybride conservé. Il devient nettement utile avec la racinisation (d) et bge-m3 (f).

### c. Filtre `lien_auto` (non retenu)

**Testé** : `--filtre direct` ne garde que les chunks du contrat et ceux dont `lien_auto` vaut `direct`, sur le chunking
par article. Les requêtes dont tous les articles attendus sont exclus restent comptées comme ratées.
Sources : `retrieval_eval_direct_multilingual-e5-small.md` et `retrieval_eval_tout_multilingual-e5-small.md`.

Sur les 32 requêtes :

| Retriever | Filtre | Chunks | hit@1 | hit@3 | hit@5 | MRR@5 | Tokens top-5 |
|---|---|---|---|---|---|---|---|
| BM25 | tout | 594 | 0.56 | 0.78 | 0.81 | 0.67 | 1360 |
| BM25 | direct | 339 | 0.47 | 0.62 | 0.69 | 0.56 | 1296 |
| Dense e5 | tout | 594 | 0.59 | 0.75 | 0.78 | 0.67 | 1140 |
| Dense e5 | direct | 339 | 0.56 | 0.69 | 0.75 | 0.64 | 1107 |
| Hybride | tout | 594 | 0.59 | 0.78 | 0.78 | 0.68 | 1341 |
| Hybride | direct | 339 | 0.50 | 0.66 | 0.66 | 0.57 | 1322 |

Le filtre rend introuvables 5 requêtes : **Q21, Q22, Q25, Q26 et Q27**. Elles n'attendent que des articles `indirect` :
L113-8, L113-9 (nullité, fausse déclaration), L114-1 (prescription), L121-18 et L124-3 (action directe).

Pour séparer ce coût de l'effet du bruit retiré, voici les mêmes scores sur les **27 autres requêtes**
(recalculés à partir des JSON) :

| Retriever | Filtre | hit@1 | hit@3 | hit@5 | MRR@5 |
|---|---|---|---|---|---|
| BM25 | tout | 0.56 | 0.78 | 0.81 | 0.67 |
| BM25 | direct | 0.56 | 0.74 | 0.81 | 0.66 |
| Dense e5 | tout | 0.63 | 0.81 | 0.85 | 0.72 |
| Dense e5 | direct | 0.67 | 0.81 | 0.89 | 0.75 |
| Hybride | tout | 0.63 | 0.78 | 0.78 | 0.70 |
| Hybride | direct | 0.59 | 0.78 | 0.78 | 0.68 |

- **Gain** : sur les 27 requêtes, retirer le bruit n'améliore que le dense, d'environ une requête. BM25 et l'hybride baissent légèrement.
- **Tokens** : le gain est minime (environ 1 à 5 %).
- **Coût** : 5 questions sur 32 deviennent impossibles à résoudre. Ce sont des règles générales du contrat d'assurance
  pourtant nécessaires à la gestion d'un sinistre auto.

**Décision** : filtre non retenu, on garde tout le corpus. `lien_auto` pourrait servir à pondérer ou réordonner
les résultats plutôt qu'à exclure des chunks.

### d. Racinisation BM25

**Testé** : `--bm25-stem` applique à BM25 (documents et requêtes) le stemmer Snowball français et retire une liste
de mots vides. L'hybride utilise alors ce BM25. Le dense e5 ne change pas.
Sources : `retrieval_eval_tout_multilingual-e5-small.md` et `retrieval_eval_tout_stem_multilingual-e5-small.md`.

| Retriever (par article) | Stem | hit@1 | hit@3 | hit@5 | MRR@5 | Tokens top-5 |
|---|---|---|---|---|---|---|
| BM25 | non | 0.56 | 0.78 | 0.81 | 0.67 | 1360 |
| BM25 | oui | 0.56 | 0.81 | 0.81 | 0.68 | 1277 |
| Hybride (e5) | non | 0.59 | 0.78 | 0.78 | 0.68 | 1341 |
| Hybride (e5) | oui | 0.62 | 0.78 | 0.81 | 0.71 | 1286 |

**Changements de rang** (rang du premier bon chunk dans le classement complet, sans stem → avec stem) :

| Requête | BM25 | Hybride (e5) |
|---|---|---|
| Q02 | 1 → 2 | = |
| Q03 | 1 → 2 | 1 → 3 |
| Q04 | 1 → 2 | = |
| Q07 | 2 → 1 | = |
| Q09 | 60 → 21 | 9 → 6 |
| Q10 | 1 → 2 | = |
| Q11 | 2 → 10 | 20 → 19 |
| Q17 | 50 → 106 | 20 → 34 |
| Q18 | 5 → 1 | 8 → 6 |
| Q19 | = | 2 → 1 |
| Q23 | 10 → 1 | 3 → 2 |
| Q25 | 2 → 8 | 2 → 4 |
| Q27 | 38 → 8 | 31 → 12 |
| Q31 | 372 → 1 | 44 → 1 |
| Q32 | 342 → 8 | 99 → 6 |

- **BM25** : 14 rangs changent, 7 s'améliorent et 7 se dégradent. Les gains corrigent des formes de mots
  différentes entre requête et article (Q31 passe du rang 372 au rang 1, Q32 de 342 à 8). Les pertes sont surtout
  des passages du rang 1 au rang 2.
- **Hybride** : 11 rangs changent, 8 s'améliorent et 3 se dégradent. Les pertes de BM25 au rang 2 sont compensées par le dense.
- **Robustesse** : le pire rang de l'hybride passe de **99 (Q32) à 34 (Q17)**.
- **Tokens** : le top-5 est environ 4 à 6 % plus léger.

**Décision** : racinisation retenue pour BM25. Elle n'est pas activée par défaut dans le script : il faut passer `--bm25-stem`.

### e. Vérification de la troncature e5

**Testé** : `multilingual-e5-small` ne lit que 512 tokens. On a compté, avec son propre tokenizer
(préfixe `passage: ` et tokens spéciaux compris), les chunks qui dépassent cette limite.
C'est une mesure ponctuelle du 20/10/2026, dont le script n'est pas versionné.

| Chunking | Chunks | Chunks > 512 tokens e5 | Plus long |
|---|---|---|---|
| Par article | 594 | 0 | 426 (art-D113-7-p1) |
| Taille fixe 500/50 | 305 | 0 | 492 |

Sur ce corpus, le tokenizer d'e5 produit moins de tokens que `cl100k`, qui sert à fixer les limites des chunks.
**Aucun chunk n'est tronqué.** La faiblesse du dense en taille fixe (MRR@5 0.41) ne vient donc pas de la troncature.
L'explication la plus probable est la dilution du sens : une fenêtre de 500 tokens mélange plusieurs articles,
et son embedding n'en représente bien aucun. C'est une interprétation : l'expérience écarte seulement la troncature.

**Décision** : aucune modification du chunking.

### f. e5-small ou bge-m3

**Testé** : le dense `BAAI/bge-m3` (sans préfixe, fenêtre de 8192 tokens) contre `intfloat/multilingual-e5-small`,
avec `--filtre tout --bm25-stem`, sur CPU.
Sources : `retrieval_eval_tout_stem_multilingual-e5-small.md`, `retrieval_eval_tout_stem_bge-m3.md` et
l'en-tête de `eval_retrieval.py` pour le temps par requête.

| Retriever (par article) | Modèle | hit@1 | hit@3 | hit@5 | MRR@5 | Tokens top-5 | Embeddings du corpus | Encodage d'une requête |
|---|---|---|---|---|---|---|---|---|
| Dense | e5-small | 0.59 | 0.75 | 0.78 | 0.67 | 1140 | 25 s | ~9 ms |
| Dense | bge-m3 | 0.62 | 0.81 | 0.84 | 0.71 | 1353 | 298 s | ~65 ms |
| Hybride | e5-small | 0.62 | 0.78 | 0.81 | 0.71 | 1286 | 25 s | ~9 ms |
| Hybride | bge-m3 | **0.69** | **0.88** | **0.91** | **0.79** | 1297 | 298 s | ~65 ms |

Le temps d'encodage d'une requête est une moyenne sur les 32 requêtes, encodées une par une après un appel
d'échauffement. Les embeddings du corpus ne sont calculés qu'une fois et peuvent être mis en cache.
Avec bge-m3, l'hybride gagne 2 requêtes en hit@1 et 3 en hit@5. Le pire rang passe de 34 à 50 (Q11).

En taille fixe, l'hybride bge-m3 obtient hit@5 = 0.88 mais seulement hit@1 = 0.44, et coûte toujours 2491 tokens.

**Décision** : bge-m3 retenu (commit 7ced6dd) et devenu le modèle par défaut du script.
`--model intfloat/multilingual-e5-small` reste disponible.

---

## 3. Erreurs restantes de la configuration finale

Source : `results/erreurs_retrieval_tout_stem_bge-m3.md`, section « Par article + Hybride (RRF) ».
**10 requêtes sur 32** n'ont pas le bon article en 1re position. 7 l'ont tout de même dans le top 5, au rang 2 ou 4.
Seules Q11, Q17 et Q25 en sortent.

Le classement par cause est une **analyse qualitative**, faite en comparant la requête à l'article attendu et à
l'article classé 1er. L'équipe doit la relire.

| Cause | Requête | Rang | Classé 1er à la place | Explication |
|---|---|---|---|---|
| Formes des mots | — | — | — | Plus aucun cas après la racinisation (voir 2.d). |
| Synonymes | Q09 « Quels documents envoyer pour déclarer un sinistre ? » | 4 | 17 — Délais de déclaration | L'article 18 parle de « pièces à fournir », pas de « documents ». L'article 17 partage « déclarer ». |
| Synonymes | Q11 « Facture de réparation gonflée… » | 50 | R125-6-1 | Les articles 23 et 25 parlent de « majoration volontaire du montant » et de « facture supérieure de plus de 30 % », pas de facture « gonflée ». |
| Connaissance manquante | Q17 « Accident survenu au Maroc… » | 19 | R211-8 | L'article 3 parle des pays de la « carte verte » sans les énumérer. Il faut savoir que le Maroc en fait partie. |
| Connaissance manquante | Q25 « Dans quel délai l'assuré peut-il agir en justice… » | 10 | L211-12 | L114-1 parle de « prescription » des « actions dérivant du contrat ». Il faut savoir qu'« agir en justice » renvoie à la prescription. |
| Bruit d'autres articles | Q03 « Délai pour déclarer un vol » | 2 | 9 — Vol et tentative de vol | L'article 9 contient « vol » et un « délai » (véhicule retrouvé sous 30 jours). |
| Bruit d'autres articles | Q06 « Accident en état d'ivresse… » | 2 | A211-11-annexe | Une annexe longue, découpée en 9 chunks, arrive en tête de plusieurs requêtes. |
| Bruit d'autres articles | Q12 « Dans quels cas un dossier doit passer en investigation ? » | 2 | 24 — Circuit de traitement | L'article 24, juste avant l'article 25 attendu, cite « investigation complémentaire » parmi les décisions possibles. |
| Bruit d'autres articles | Q14 « Délai de déclaration après une inondation… cat. nat. » | 2 | L125-1 | L125-1 parle de catastrophes naturelles et de délais (publication de l'arrêté), mais pas du délai de déclaration de l'assuré. |
| Bruit d'autres articles | Q27 « La victime peut-elle réclamer directement… » | 2 | A211-11-annexe | Même annexe que Q06. En plus, L124-3 parle de « tiers lésé » plutôt que de « victime ». |
| Vérité terrain discutable | Q04 « Quelle franchise en cas de responsabilité partielle ? » | 2 | 20 — Tableau des franchises | L'article 21 attendu renvoie explicitement aux montants de l'article 20 : un article 20 en 1re position n'est pas une mauvaise réponse pour le LLM. Il y a aussi un écart de vocabulaire (« partielle » / « partagée »). |

Bilan : 5 cas de bruit, 2 de synonymes, 2 de connaissance manquante, 1 de vérité terrain discutable et aucun de forme
des mots. L'annexe A211-11 revient deux fois en 1re position : elle mérite un traitement spécifique,
par exemple une pénalité ou un chunking dédié.

---

## 4. Configuration retenue et suite

**Retenu** : chunking « Par article », hybride RRF (k = 60), BM25 avec racinisation française (`--bm25-stem`) et dense `BAAI/bge-m3`,
sur tout le corpus (`--filtre tout`).

| hit@1 | hit@3 | hit@5 | MRR@5 | Tokens top-5 |
|---|---|---|---|---|
| 0.69 | 0.88 | 0.91 | 0.79 | 1297 |

Commande : `python rag/eval_retrieval.py --bm25-stem`. bge-m3 est le modèle par défaut, mais la racinisation ne l'est pas.

**Pourquoi** :
- C'est la meilleure configuration mesurée sur toutes les métriques de qualité.
- Elle envoie environ deux fois moins de tokens au LLM que la taille fixe.
- Son coût reste raisonnable sur CPU : environ 5 min d'indexation, une seule fois, et environ 65 ms par requête,
  négligeables à côté de l'appel au LLM.
- BM25 et le dense se complètent : dans le tableau croisé, chacun rate seul 5 requêtes que l'autre réussit,
  et l'hybride n'introduit aucune erreur qui lui soit propre.

**Reste à faire** :
- **Reformulation des questions par le LLM dans le Policy Agent**, avant le retrieval. Elle doit traiter les
  synonymes (Q09, Q11) et la connaissance manquante (Q17, Q25), en traduisant la question de l'utilisateur dans le
  vocabulaire du contrat et du Code : « facture gonflée » → « majoration du montant », « agir en justice » →
  « prescription », « Maroc » → « carte verte ».
- **Traiter le bruit** de l'annexe A211-11, par exemple avec une pénalité, un chunking dédié ou une pondération par `lien_auto`.
- **Revoir la vérité terrain** de Q04, en acceptant aussi l'article 20.
- **Agrandir le jeu de requêtes** (section 5).

---

## 5. Limites

- **32 requêtes seulement** : une requête vaut environ 0,03 sur hit@k. Un écart d'une ou deux requêtes, soit 0,03 à 0,06,
  n'est pas significatif et ne doit pas être présenté comme un gain établi. C'est le cas, par exemple, de la racinisation
  seule sur BM25 ou du filtre sur le dense. Seuls les écarts plus larges et cohérents sur toutes les métriques
  sont des tendances crédibles : par article contre taille fixe, bge-m3 + hybride contre e5.
- **Questions rédigées par l'équipe**, qui connaît le corpus. Leur vocabulaire est sans doute plus proche des articles
  que celui de vrais assurés, et les résultats sont probablement optimistes.
- **Contrat fictif** : les 26 articles du contrat ont été rédigés pour le projet. Seuls les articles du Code des assurances
  sont des textes réels.
- **Vérité terrain** : chaque requête n'a qu'un ou quelques articles attendus, et certaines réponses voisines
  pourraient être acceptées (voir Q04).
- **Matériel** : temps mesurés sur une seule machine, sur CPU.

---

## Historique des commits (branche `ragAgent`)

| Commit | Contenu |
|---|---|
| 3d8a55c | Regroupe plusieurs expériences : **hybride RRF, analyse d'erreurs détaillée, filtre `lien_auto` et racinisation** (`--bm25-stem`), plus les résultats par filtre. |
| 7ac528c | Corpus Code des assurances, chunking multi-fichiers avec découpage des articles longs, 32 requêtes. Ce commit aurait dû précéder 3d8a55c, dont les résultats ont été produits avec ces fichiers. |
| 7ebd7b9 | Documente la configuration retenue à ce stade (e5-small). |
| 0b990dc | Évaluation bge-m3, mesure du temps d'embeddings. |
| 7ced6dd | bge-m3 retenu comme modèle dense par défaut ; fichiers de résultats suffixés par le nom du modèle. |
