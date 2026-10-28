# Bibliothèque de prompts et règles — AI Claims Agent

**Version :** 1.0 · **Date :** 28 octobre 2026
**Référence du code :** `backend/claims/agents.py`
**Modèles :** Document et Policy `qwen2.5:3b`; Vision `llava:7b`. Fraud et Decision sont des fonctions Python déterministes.

Cette bibliothèque consigne les consignes livrées, leur technique, les erreurs observées et les corrections. Les différences présentées sont des itérations d’ingénierie documentées ; elles ne constituent pas un benchmark comparatif contrôlé des modèles. Les prompts ne demandent pas au modèle de révéler son raisonnement privé : les sorties exposent des champs, des éléments justificatifs et les références utiles.

## P1 — Extraction des faits (Document Agent)

**Rôle et technique.** Extraire les faits explicitement présents dans le formulaire, les PDF et la transcription audio. La sortie est contrainte par le schéma Pydantic `DocumentFacts`. Consigne d’extraction conservatrice et sortie JSON structurée.

**Prompt système version 1 (actuel).**

> Extrais les faits du sinistre. N'invente rien; utilise null ou une liste vide si une donnée manque.

Le message utilisateur ajoute les champs du dossier, les textes PDF sélectionnés après comparaison pypdf/OCR et les transcriptions audio. Les photos restent réservées à Vision.

| Itération | Avant | Échec / observation | Après et correctif |
|---|---|---|---|
| PDF | pypdf seul, extraction de la couche texte. | Un PDF scanné sans couche texte revient vide ; les informations du document ne parviennent pas à l’extraction structurée. | pypdf et Tesseract sont exécutés sur les pages ; la sortie contient les deux extraits, leur similarité et les segments identiques. pypdf est retenu si son texte dépasse 80 caractères, sinon l’OCR si celui-ci est plus riche. |
| Audio | Transcription Faster-Whisper transmise telle quelle au modèle. | Une transcription bruitée peut contenir des mots erronés ; elle n’est pas une preuve fiable sans écoute ou pièce écrite correspondante. | Conserver la transcription et ses métadonnées de langue, durée et probabilité ; l’extraction ne doit pas compléter les champs absents par supposition. La qualité de transcription reste à mesurer sur un corpus audio annoté. |

**Validation.** Deux tests unitaires couvrent la comparaison des textes et le choix pypdf/OCR lorsque la couche native est vide. Un test d’intégration Docker sur une page PDF image-only a confirmé zéro texte pypdf, 47 caractères OCR et la sélection OCR. Ce petit test synthétique valide le chemin d’exécution, pas la qualité sur des formulaires réels.

## P2 — Observation visuelle (Vision Agent)

**Rôle et technique.** Décrire les dommages visibles dans un maximum de six photos. llava reçoit les images directement ; la normalisation conserve les seules zones `rear`, `front`, `left`, `right`. Aucune zone hors champ n’est inférée depuis le récit.

**Prompt système (actuel).**

> Tu observes des photos de véhicule. Décris seulement ce qui est visible, sans déduire les parties hors champ. Réponds en JSON.

**Prompt utilisateur (actuel).**

> Decris ce qui est visiblement endommage sur ces photos. Indique seulement les zones du vehicule que tu peux voir: rear, front, left ou right. JSON seulement: `{"damaged_areas":[]}`. Ne devine pas les parties hors champ.

| Itération | Avant | Échec / observation | Après et correctif |
|---|---|---|---|
| Vision | Demande générale de décrire et classifier les dommages. | Un essai sur photos a signalé « front » alors que la déclaration et les vues identifiaient l’arrière. Un premier cas Élodie a été envoyé à examen à cause de cette contradiction. | Demander uniquement les zones effectivement visibles, interdire l’inférence hors champ, puis contrôler le résultat contre les noms de vues explicites. Une contradiction photo/vue rend l’analyse incomplète et déclenche l’examen, au lieu d’être comptée comme fraude établie. |

**Limite.** Le nom du fichier est seulement un contrôle d’anomalie ; il ne prouve pas la zone endommagée. La confiance VLM n’est pas calibrée statistiquement.

## P3 — Vérification contractuelle (Policy/RAG Agent)

**Rôle et technique.** Répondre depuis les cinq passages récupérés dans les Conditions générales AXA et, si présent, le document client de Conditions particulières. Le modèle reçoit une consigne de classification prudente et un schéma `PolicyAnalysis`.

**Prompt système (actuel).**

> Vérifie la couverture uniquement avec les extraits contractuels AXA fournis. Cherche en priorité dommages au véhicule, collision et dommages tous accidents. `coverage_status`: `covered` uniquement si la garantie souscrite est confirmée dans les Conditions particulières du client; `excluded` uniquement si une exclusion explicite correspond au sinistre; sinon `insufficient_information`. Si les Conditions particulières du client sont absentes, réponds obligatoirement `insufficient_information`. Dans `applicable_articles`, cite les pages sous la forme « Page 42 ».

**Technique.** RAG avec passages issus du corpus, génération structurée, et règle explicite d’abstention si les Conditions particulières manquent. Une vérification Python supplémentaire ne confirme une garantie collision que si le numéro de police correspond et que le document client dit explicitement que la garantie est souscrite/active.

| Itération | Avant | Échec / observation | Après et correctif |
|---|---|---|---|
| Statut de couverture | Le statut et l’explication du modèle étaient utilisés ensemble comme une réponse unique. | Sur le dossier Élodie, l’explication décrivait une garantie active, mais le statut JSON était `insufficient_information`; la décision affichée était « À examiner ». | Garder la consigne d’abstention ci-dessus et appliquer le contrôle déterministe du numéro de police et du libellé explicite de garantie. Le texte explicatif du modèle seul ne peut plus confirmer la couverture. |
| Référence | Le modèle pouvait renvoyer un numéro d’article sans page exploitable. | L’utilisateur ne pouvait pas retrouver rapidement la clause dans le PDF. | Demander une référence « Page N » et transmettre le passage avec page, section et source. |

**Limites.** La vérification déterministe couvre quelques formulations et n’est pas un moteur complet d’interprétation contractuelle. Une police ambiguë doit rester `insufficient_information`.

## R1 — Contrôle de cohérence (Fraud Agent, sans prompt LLM)

Le terme « Fraud » désigne le nœud de contrôle du prototype : il signale des contradictions documentées et ne conclut pas juridiquement à une fraude.

| Règle actuelle | Points | Garde-fou |
|---|---:|---|
| Zones du récit et zones du VLM disjointes | +50 | Seulement si Vision est complète ; une vision en erreur donne un score final `null`. |
| Pièce requise signalée manquante | +25 | Conserver les noms des pièces manquantes comme éléments de justification. |
| Total | Plafonné à 100 | `min(100, somme)` ; vision incomplète signifie « Non évalué », pas zéro. |

**Avant / après.** Avant, un score partiel pouvait être interprété comme score final même sans analyse photo. Après, le statut incomplet bloque la publication du score final. Les scores sont des règles de démonstration, pas une probabilité calibrée de fraude.

## R2 — Recommandation (Decision Agent, sans prompt LLM)

| Priorité | Condition | Recommandation |
|---:|---|---|
| 1 | Une exclusion contractuelle explicite s’applique | `REJECT` |
| 2 | Couverture inconnue, analyse Fraud incomplète ou risque positif | `INVESTIGATE` |
| 3 | Couverture confirmée, analyse complète et aucun risque relevé | `ACCEPT` |

**Itération observée.** Un dossier sans photo avait un risque non évalué. Il pouvait être confondu avec `0/100`. Le résultat est désormais représenté par `null` et le nœud Decision force l’examen lorsque l’analyse est incomplète.

## Historique de version

| Version | Modification |
|---|---|
| 1.0 — 28/10/2026 | Prompts Document, Vision et Policy alignés sur le code ; consignes d’abstention, limites, cas d’échec et règles Fraud/Decision consignés. Ajout de la comparaison pypdf/OCR au traitement documentaire. |
