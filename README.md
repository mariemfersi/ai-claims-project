# AI Claims Agent — dépôt de travail (v0, semaine 1)

Automatisation de l'analyse des dossiers de sinistre auto avec n8n, multi-agents, RAG et multimodalité.
Projet Advanced Deep Learning (AI Automation), ESPRIT 5DS, 2026-2027.

## État d'avancement

| Bloc | Fait en v0 | Reste à faire |
|---|---|---|
| Cadrage, architecture, rôles | Oui | Valider au suivi |
| Dossiers synthétiques | 10 dossiers décrits (JSON) | Produire les PDF (constats, factures), photos, audio |
| Corpus RAG | 26 articles (≈ 4 000 tokens) | Ajouter des CG publiques réelles (30-100 pages) |
| Chunking | 2 stratégies codées | Tester d'autres tailles, reranking |
| Évaluation retrieval | 20 requêtes, hit@k + MRR, premiers résultats | Refaire sur le corpus complet, bge-m3, filtres |
| Prompts | P1 et P2 v1 rédigés | Tests, échecs, v2 ; P3 à P7 |
| Workflow n8n | Squelette + Intake Agent branché | Agents 2 à 7, gestion d'erreurs complète |
| Vector store | — | Qdrant (Docker) |

## Arborescence

```
data/corpus/conditions_generales_auto.md   corpus de travail (CG structurées par article)
data/dossiers/dossiers_synthetiques.json   10 dossiers de test + vérité terrain
rag/chunking.py                            taille fixe 500/50 et découpage par article
rag/test_queries.json                      20 requêtes de test avec articles attendus
rag/eval_retrieval.py                      évaluation hit@1/3/5, MRR@5, tokens envoyés
results/retrieval_eval.md                  résultats de la première évaluation
prompts/PROMPTS.md                         bibliothèque de prompts versionnée
n8n/claims_agent_workflow_v0.json          workflow à importer dans n8n
scripts/send_dossier.py                    envoie un dossier de test au webhook
```

## Lancer l'évaluation du retrieval

```bash
pip install -r requirements.txt
python rag/eval_retrieval.py                       # multilingual-e5-small (rapide)
python rag/eval_retrieval.py --model BAAI/bge-m3   # modèle cible, plus lourd (~2 Go)
```

## Lancer le workflow n8n

1. Démarrer n8n : `npx n8n` (ou Docker : `docker run -it --rm -p 5678:5678 n8nio/n8n`), puis ouvrir http://localhost:5678
2. Menu « Import from file » → `n8n/claims_agent_workflow_v0.json`
3. Créer une clé API Gemini (gratuite sur Google AI Studio), puis dans le nœud « 1. Claim Intake Agent » créer un credential « Header Auth » : nom `Authorization`, valeur `Bearer VOTRE_CLE`
4. Cliquer sur « Test workflow », puis dans un terminal : `python scripts/send_dossier.py D01`
5. La réponse contient le JSON normalisé de l'Intake Agent et le journal des étapes

Les nœuds 2 à 7 sont des emplacements vides (NoOp) : la structure parallèle puis séquentielle est déjà en place.
