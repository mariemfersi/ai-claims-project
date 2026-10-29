DOSSIER DE TEST - INCOHÉRENCE VISUELLE

Toutes les personnes, adresses, immatriculations, contrats, entreprises, montants, déclarations et circonstances de ce dossier sont fictifs. Les photos sont des images générées, pas des preuves réelles.

IDENTITÉ À SAISIR DANS L'APPLICATION
Nom : Lucas Petit
Nationalité : française (personnage fictif)
Adresse : 42 rue Paradis, 13006 Marseille, France
Assureur déclaré : AXA France
Contrat : AXA-FR-DEMO-2026-0135
Véhicule : Peugeot 208 grise fictive
Immatriculation : GH-732-VB (format français, plaque fictive)
Date : 20/10/2026
Lieu : Boulevard Baille, Marseille

DESCRIPTION À SAISIR
Le 20 octobre 2026 vers 15 h 10, boulevard Baille à Marseille, un utilitaire a reculé et heurté l'avant de ma voiture alors que j'étais à l'arrêt. Le pare-chocs avant est enfoncé, le capot est marqué et le phare avant gauche est cassé. Personne n'est blessé. La voiture peut encore rouler.

PIÈCES À JOINDRE (NE PAS JOINDRE CE README)
01_formulaire_declaration.pdf - déclaration de choc à l'avant
02_constat_amiable.pdf - compte rendu de test, choc déclaré à l'avant
03_devis_reparation.pdf - devis fictif de réparations à l'avant
04_photo_vue_arriere.png - dommages visibles à l'arrière
05_photo_degats_gros_plan.png - gros plan des dégâts arrière
06_photo_vue_laterale.png - vue latérale montrant les dégâts arrière
07_declaration_audio.wav - déclaration en français indiquant un choc à l'avant

ANOMALIE ATTENDUE
Le récit et les PDF décrivent un dommage à l'avant ; la vision des trois photos doit identifier des dommages à l'arrière. La règle damage_location_mismatch ajoute 50 points de risque. Si le Document Agent signale aussi une pièce manquante, le score peut ajouter 25 points supplémentaires. Cela doit mener à « À examiner », pas à une conclusion automatique de fraude.

CONDITION DE TEST
Ollama et le VLM doivent être actifs pour que Vision Agent regarde réellement les photos. En mode fallback local, la zone de dommage est déduite du texte de la déclaration ; le désaccord visuel ne sera donc pas détecté. Les Conditions particulières AXA ne sont pas fournies : le Policy/RAG Agent peut aussi recommander une vérification de couverture.
