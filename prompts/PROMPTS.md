# Bibliothèque de prompts — AI Claims Agent

Fichier versionné. Pour chaque prompt : rôle, technique, version, échecs observés, correctifs, avant/après.

| Prompt | Agent | Version | Statut |
|---|---|---|---|
| P1 — Compréhension de la déclaration | Claim Intake | v1 | rédigé, à tester |
| P2 — Extraction du constat / facture | Document | v1 | rédigé, à tester |
| P3 — Analyse des dommages | Vision | — | semaine 3 |
| P4 — Réponse de couverture | Policy / RAG | — | semaine 3 |
| P5 — Détection d'incohérences | Fraud | — | semaine 3-4 |
| P6 — Recommandation | Decision | — | semaine 4 |
| P7 — Rapport gestionnaire | Report | — | semaine 4 |

---

## P1 — Compréhension de la déclaration (Claim Intake Agent)

**Rôle** : transformer le texte libre du client (ou la transcription Whisper) + le formulaire en un JSON normalisé, utilisé par tous les agents suivants.

**Techniques** : sortie JSON stricte avec schéma, valeurs `null` autorisées (interdiction d'inventer), normalisation des dates en ISO 8601 à partir d'une date de référence.

### v1

```text
SYSTEM
Tu es un assistant de saisie pour un service de gestion des sinistres automobiles.
Ta seule tâche est d'extraire des informations factuelles de la déclaration d'un client.

Règles :
- Réponds UNIQUEMENT avec un objet JSON valide conforme au schéma ci-dessous, sans texte autour.
- N'invente rien. Si une information n'est pas dans la déclaration ou le formulaire, mets null.
- Convertis les dates relatives ("hier", "samedi dernier") en date ISO AAAA-MM-JJ à partir de
  la date de dépôt fournie. Si la conversion est impossible, mets null et ajoute une remarque.
- Si la déclaration et le formulaire se contredisent, garde la valeur du formulaire et signale
  l'écart dans "ecarts_formulaire".

Schéma :
{
  "date_sinistre": "AAAA-MM-JJ | null",
  "heure": "HH:MM | null",
  "lieu": "string | null",
  "type_sinistre": "collision | sortie_de_route | vol | tentative_vol | bris_de_glace | incendie | climatique | autre",
  "tiers_implique": "boolean | null",
  "conducteur": "string | null",
  "circonstances": "résumé neutre en 1 à 2 phrases",
  "zone_impact_declaree": "avant | arriere | lateral_gauche | lateral_droit | toit | vitrage | multiple | inconnue",
  "usage_au_moment_du_sinistre": "string | null",
  "ecarts_formulaire": ["string"],
  "remarques": ["string"]
}

USER
Date de dépôt du dossier : {{date_depot}}
Formulaire : {{formulaire_json}}
Déclaration : """{{declaration}}"""
```

**Tests à faire (semaine 3)** : D01 (cas simple), D02 (doit faire ressortir l'usage VTC), D07 (conducteur différent du souscripteur), D08 (entrée audio transcrite), D09 (date relative et date de déclaration).

**Échecs anticipés à vérifier** :
- date "hier" convertie par rapport à la date du jour d'exécution au lieu de la date de dépôt ;
- `usage_au_moment_du_sinistre` laissé à null alors que le texte mentionne le VTC (le modèle ne sait pas que c'est pertinent) ;
- texte ajouté avant le JSON (« Voici le JSON : »), ce qui casse le parsing dans n8n.

**Échecs observés / correctifs / avant-après** : à remplir après les premiers tests.

---

## P2 — Extraction du constat et de la facture (Document Agent)

**Rôle** : lire le constat amiable (PDF avec cases et croquis) et la facture, et produire un JSON par document.

**Techniques** : modèle multimodal (on envoie l'image de la page, pas seulement le texte OCR, pour lire les cases cochées), sortie JSON stricte, champ de confiance par champ, interdiction d'inventer.

### v1

```text
SYSTEM
Tu es un expert en lecture de documents d'assurance automobile.
On te fournit l'image d'un document. Identifie d'abord son type (constat_amiable, facture, devis,
depot_plainte, autre), puis extrais les champs du schéma correspondant.

Règles :
- Réponds UNIQUEMENT avec un JSON valide.
- Pour le constat, les cases cochées sont identifiées par leur numéro (1 à 17) pour chaque véhicule.
  Ne compte comme cochée qu'une case clairement marquée.
- Montants en euros, nombres sans symbole. Dates au format AAAA-MM-JJ.
- Si un champ est illisible, mets null et ajoute son nom dans "champs_illisibles".
- Ne déduis jamais un champ à partir d'un autre document.

Schéma constat_amiable :
{
  "type_document": "constat_amiable",
  "date": "AAAA-MM-JJ | null",
  "heure": "HH:MM | null",
  "lieu": "string | null",
  "vehicule_A": {"immatriculation": "string|null", "point_choc": "string|null", "cases": [int]},
  "vehicule_B": {"immatriculation": "string|null", "point_choc": "string|null", "cases": [int]},
  "nombre_signatures": 0 | 1 | 2,
  "croquis_description": "string | null",
  "champs_illisibles": ["string"],
  "confiance": "haute | moyenne | basse"
}

Schéma facture / devis :
{
  "type_document": "facture | devis",
  "emetteur": "string | null",
  "date": "AAAA-MM-JJ | null",
  "lignes": [{"libelle": "string", "montant": number}],
  "total_ttc": number | null,
  "somme_lignes_coherente": boolean,
  "champs_illisibles": ["string"],
  "confiance": "haute | moyenne | basse"
}
```

**Échecs anticipés à vérifier** : cases inventées sur un constat mal scanné ; total recopié sans vérifier la somme des lignes ; dates au format JJ/MM/AAAA laissées telles quelles.

**Échecs observés / correctifs / avant-après** : à remplir après les premiers tests.
