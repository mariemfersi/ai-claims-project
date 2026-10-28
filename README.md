# AI Claims Agent

Prototype universitaire d'automatisation des sinistres automobiles.

## Architecture

- React et Vite pour l'interface.
- Django REST Framework pour les dossiers, les fichiers et les agents.
- n8n pour orchestrer automatiquement le pipeline.
- PostgreSQL pour les données métier.
- Ollama pour exécuter localement les LLM, le VLM et les embeddings.
- Trois agents parallèles : Document, Vision et Policy RAG.
- Deux agents séquentiels : Fraud puis Decision.

## Démarrage avec Docker

1. Lancer Ollama Desktop.
2. Installer les modèles configurés dans `.env` : `qwen2.5:3b`, `llava:7b` et `nomic-embed-text:latest` (ou remplacer les variables `OLLAMA_*_MODEL` par les noms présents dans Ollama).
3. Copier `.env.example` vers `.env` si le fichier n'existe pas.
4. Lancer `docker compose up --build`.
5. Ouvrir React sur `http://localhost:5173`.
6. Ouvrir n8n sur `http://localhost:5678` pour observer les exécutions.

Le workflow `n8n/ai-claims-workflow.json` est importé et publié automatiquement au démarrage.

L'API Django est disponible sur `http://localhost:8000/api/`.

## Email de transmission des dossiers

Quand un dossier « À examiner » est transmis à un responsable depuis React, Django lui envoie automatiquement un email récapitulatif avec les pièces jointes (jusqu'à 20 Mo au total). Configure un compte SMTP expéditeur dans `.env` avant de transmettre : `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL` et `DEFAULT_FROM_EMAIL`. Pour Gmail, utilise un mot de passe d'application, pas le mot de passe normal. Après modification de `.env`, redémarre avec `docker compose up -d backend`. L'état de l'envoi apparaît dans le dossier et l'email peut être renvoyé depuis la fiche.

## Parcours de démonstration

1. Créer un dossier depuis React.
2. Django enregistre le dossier et déclenche le webhook n8n.
3. n8n appelle les trois agents spécialisés en parallèle.
4. n8n appelle Fraud Agent puis Decision Agent.
5. n8n renvoie le résultat à Django.
6. React interroge le statut et affiche la décision automatiquement.

## Développement sans n8n

Définir `N8N_WEBHOOK_URL=` dans `.env`. Les dossiers restent au statut `SUBMITTED`, et les endpoints internes des agents peuvent être testés séparément.

## Modèles

- Document Agent : `qwen2.5:3b`; extraction de chaque PDF par pypdf et Tesseract OCR français/anglais, comparaison des deux résultats dans la sortie de l’agent, puis sélection du texte natif s’il est exploitable ou de l’OCR pour les PDF scannés.
- Déclarations audio : `faster-whisper` avec le modèle local `small` en français, CPU int8.
- Vision Agent : `llava:7b`.
- Policy RAG Agent : `qwen2.5:3b` et `nomic-embed-text:latest`.

Ollama est l'unique moteur d'IA du projet. Si Ollama est fermé ou si un modèle manque, les agents reviennent à leur fallback déterministe sans arrêter le workflow.

Le Policy RAG utilise les Conditions générales réelles et publiques AXA France « Mon Auto », version septembre 2026. Le PDF officiel de 104 pages est conservé dans `backend/claims/corpus/axa_mon_auto_septembre_2026.pdf`; sa provenance et son URL sont décrites dans `backend/claims/policy_corpus.json`. Les pages 5 à 103 sont extraites et indexées, puis les cinq pages les plus proches de la déclaration sont transmises au modèle. La couverture finale dépend néanmoins des Conditions particulières du contrat de l'assuré.

La comparaison PDF est visible dans le résultat JSON du Document Agent : texte pypdf, texte OCR, similarité, segments identiques et méthode retenue. Tesseract et la langue française sont installés dans l’image Docker du backend. Voir `output/evaluation/evaluation_rag.md` pour l’évaluation de recherche et `output/documents/bibliotheque_prompts.md` pour la bibliothèque de prompts versionnée.

Pour reproduire le benchmark avec le modèle d’embeddings local : `python output/evaluation/evaluate_rag.py --ollama --model nomic-embed-text:latest` (Ollama doit être lancé). Sans le drapeau `--ollama`, le script calcule uniquement le baseline lexical.

Le plan de démonstration de 15 minutes et la préparation des questions de soutenance sont dans `output/documents/plan_demo_15min.md`.

