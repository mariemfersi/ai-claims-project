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
2. Installer `qwen3:4b`, `qwen3-vl:4b` et `qwen3-embedding:0.6b` avec `ollama pull`.
3. Copier `.env.example` vers `.env` si le fichier n'existe pas.
4. Lancer `docker compose up --build`.
5. Ouvrir React sur `http://localhost:5173`.
6. Ouvrir n8n sur `http://localhost:5678` pour observer les exécutions.

Le workflow `n8n/ai-claims-workflow.json` est importé et publié automatiquement au démarrage.

L'API Django est disponible sur `http://localhost:8000/api/`.

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

- Document Agent : `qwen3:4b`, avec PyPDF pour le texte natif et le VLM/OCR pour les images.
- Vision Agent : `qwen3-vl:4b`.
- Policy RAG Agent : `qwen3:4b` et `qwen3-embedding:0.6b`.

Ollama est l'unique moteur d'IA du projet. Si Ollama est fermé ou si un modèle manque, les agents reviennent à leur fallback déterministe sans arrêter le workflow.

