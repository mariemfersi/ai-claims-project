# Plan de démonstration — 15 minutes

Préparer les services et un dossier fictif complet avant la séance. Ne pas utiliser de vraies données d’assurés. Remplacer les rôles ci-dessous par les prénoms de l’équipe ; chaque membre doit connaître l’ensemble du parcours.

| Temps | Partie | Démonstration |
|---|---|---|
| 0–2 min | Contexte et architecture | Présenter React, Django, n8n, Ollama, les cinq agents et le flux parallèle puis séquentiel. |
| 2–5 min | Dépôt d’un dossier | Soumettre le formulaire, un PDF, des photos et éventuellement l’audio ; rappeler que les données sont fictives. |
| 5–8 min | Document, OCR et Vision | Montrer la chronologie ; ouvrir la comparaison pypdf/OCR avec les textes extraits et le passage commun ; commenter l’observation image par image. |
| 8–11 min | Policy/RAG, Fraud et Decision | Montrer le corpus AXA, les pages récupérées, les Conditions particulières du dossier, les règles du score et la recommandation. |
| 11–13 min | Traçabilité et cas incomplet | Montrer les pièces du dossier et l’historique. Utiliser un cas sans photo pour expliquer pourquoi le risque est « Non évalué », et non égal à zéro. |
| 13–15 min | Évaluation et limites | Présenter le benchmark RAG sur huit requêtes, les deux segmentations, les limites de l’échantillon et les protections requises avant production. |

## Répartition à compléter

- Membre 1 : architecture, outils et démarrage.
- Membre 2 : Document Agent, pypdf, OCR et audio.
- Membre 3 : Vision, RAG et sources contractuelles.
- Membre 4 : Fraud, Decision, score et limites.
- Si l’équipe compte cinq ou six personnes, ajouter un ou deux intervenants pour la traçabilité, l’évaluation et la sécurité.

Les créneaux se chevauchent avec la préparation : chaque membre prépare une réponse courte sur les choix et limites des autres parties. La séance comprend ensuite 10 minutes de questions du jury.
