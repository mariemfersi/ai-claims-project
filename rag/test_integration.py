"""Tests de rag/integration.py avec un Policy Agent simulé : aucun appel LLM, aucun Qdrant.

Usage :
    python rag/test_integration.py

Vérifie que la sortie de policy_agent_pour_backend a les clés lues par la branche ines :
policy_agent(claim) dans backend/claims/agents.py, decision_agent (coverage_status,
explanation, references) et frontend/src/App.jsx (references : page, section, source, text).
"""
import datetime, json, os, sys, types, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import integration

# Clés renvoyées par policy_agent(claim) dans backend/claims/agents.py (branche ines)
CLES_BACKEND = {"agent", "engine", "model", "embedding_model", "coverage_status", "references",
                "retrieved_chunks", "retrieval_query", "explanation", "missing_information",
                "confidence", "diagnostic_error"}
CLES_AJOUTEES = {"articles_cites", "franchise", "trace"}
CLES_REFERENCE = {"page", "section", "source", "text"}  # lues par App.jsx
STATUTS_BACKEND = {"covered", "excluded", "insufficient_information"}

CLAIM = {"customer_name": "Sami Ben Ali", "policy_number": "AUTO-2026-001",
         "incident_date": datetime.date(2026, 10, 3), "location": "Tunis",
         "description": "Arrêté au feu rouge, j'ai été percuté à l'arrière par une autre voiture."}
CP = {"garanties": ["responsabilite_civile", "dommages_collision"], "usage_declare": "privé et trajet travail",
      "conducteurs_designes": ["Sami Ben Ali"], "date_souscription": "2025-01-15"}

FOURNIS = [{"article": "7", "titre": "Dommages collision", "source": "contrat", "score": 0.05, "questions": [1]},
           {"article": "15", "titre": "Franchises", "source": "contrat", "score": 0.04, "questions": [3]},
           {"article": "L113-2", "titre": "Obligations de l'assuré", "source": "code_assurances", "score": 0.03,
            "questions": [4]},
           {"article": "20", "titre": "Exclusions", "source": "contrat", "score": 0.02, "questions": [2]}]
CHUNKS = [{"text": "Article 7. La garantie dommages collision couvre " + "x" * 700,
           "metadata": {"article": "7", "partie": 1}},
          {"text": "Article 15. Franchise de 300 DT.", "metadata": {"article": "15"}},
          {"text": "Article L113-2. L'assuré est obligé de déclarer le sinistre.", "metadata": {"article": "L113-2"}}]


def reponse(verdict, cites=("7", "15"), confiance="haute", justification="Couvert par la garantie collision (7)."):
    return {"garantie_applicable": {"nom": "dommages collision", "article": "7"}, "exclusions_applicables": [],
            "franchise": {"montant": "300 DT", "article": "15", "detail": "franchise fixe"},
            "verdict_couverture": verdict, "articles_cites": list(cites), "justification": justification,
            "confiance": confiance,
            "trace": {"modele": "gemini-test", "sous_questions": [{"id": 1, "theme": "garantie", "originale": "Q1 ?"},
                                                                   {"id": 2, "theme": "exclusions", "originale": "Q2 ?"}],
                      "articles_fournis": FOURNIS, "appels": [], "avertissements": []}}


class TestIntegration(unittest.TestCase):
    def lancer(self, claim, analyse=None, erreur=None):
        """Lance l'adaptateur avec policy_agent et retriever simulés ; renvoie (sortie, intake reçu)."""
        recu = {}

        def fausse_analyse(intake, cache=True):
            recu["intake"] = intake
            if erreur:
                raise erreur
            return analyse

        modules = {"policy_agent": types.SimpleNamespace(analyse_couverture=fausse_analyse),
                   "retriever": types.SimpleNamespace(_state={"chunks": CHUNKS, "model_name": "BAAI/bge-m3"})}
        with mock.patch.dict(sys.modules, modules):
            sortie = integration.policy_agent_pour_backend(claim)
        return sortie, recu.get("intake")

    def verifier_format(self, sortie):
        self.assertTrue(CLES_BACKEND | CLES_AJOUTEES <= sortie.keys(), CLES_BACKEND | CLES_AJOUTEES - sortie.keys())
        self.assertIn(sortie["coverage_status"], STATUTS_BACKEND)
        self.assertEqual(sortie["agent"], "policy_rag")
        self.assertIsInstance(sortie["explanation"], str)
        self.assertTrue(sortie["explanation"])
        self.assertIsInstance(sortie["missing_information"], list)
        self.assertIsInstance(sortie["confidence"], float)
        self.assertTrue(0 <= sortie["confidence"] <= 1)
        for ref in sortie["references"] + sortie["retrieved_chunks"]:
            self.assertTrue(CLES_REFERENCE <= ref.keys())
            self.assertIn(ref["source"], {"Contrat", "Code des assurances"})
            self.assertIn(f"Article {ref['article']}", ref["section"])
        json.dumps(sortie, ensure_ascii=False)  # stocké tel quel dans le JSONField agent_results

    def test_couvert(self):
        sortie, intake = self.lancer({**CLAIM, "conditions_particulieres": CP}, reponse("couvert"))
        self.verifier_format(sortie)
        self.assertEqual(sortie["coverage_status"], "covered")
        self.assertEqual(sortie["missing_information"], [])
        self.assertEqual([r["article"] for r in sortie["references"]], ["7", "15"])
        self.assertEqual(sortie["references"][0]["source"], "Contrat")
        self.assertTrue(sortie["references"][0]["text"].endswith("…"))  # extrait tronqué à 600 caractères
        self.assertEqual(sortie["franchise"]["montant"], "300 DT")
        self.assertEqual(sortie["articles_cites"], ["7", "15"])
        self.assertEqual(sortie["confidence"], 0.9)
        self.assertIsNone(sortie["diagnostic_error"])
        self.assertEqual(sortie["retrieval_query"], "Q1 ?\nQ2 ?")
        # intake construit à partir des champs du modèle Claim
        self.assertEqual(intake["date_sinistre"], "2026-10-03")
        self.assertEqual(intake["lieu"], "Tunis")
        self.assertEqual(intake["circonstances"], CLAIM["description"])
        self.assertEqual(intake["type_sinistre"], "collision")  # « feu rouge » ne donne pas « incendie »
        self.assertEqual(intake["conditions_particulieres"], CP)

    def test_statuts(self):
        attendus = {"couvert": "covered", "partiel": "insufficient_information", "non_couvert": "excluded",
                    "indetermine": "insufficient_information"}
        for verdict, statut in attendus.items():
            with self.subTest(verdict=verdict):
                sortie, _ = self.lancer({**CLAIM, "conditions_particulieres": CP}, reponse(verdict))
                self.verifier_format(sortie)
                self.assertEqual(sortie["coverage_status"], statut)
                self.assertEqual(sortie["verdict_couverture"], verdict)

    def test_partiel_en_investigation(self):
        # covered sans fraude → ACCEPT automatique dans decision_agent : le partiel doit être examiné
        rep = reponse("partiel", justification="Responsabilité partagée à 50 % (15).")
        sortie, _ = self.lancer({**CLAIM, "conditions_particulieres": CP}, rep)
        self.assertEqual(sortie["coverage_status"], "insufficient_information")
        self.assertEqual(sortie["verdict_couverture"], "partiel")
        self.assertEqual(sortie["explanation"], "Couverture partielle : Responsabilité partagée à 50 % (15).")
        self.assertIsNone(sortie["diagnostic_error"])
        self.assertEqual([r["article"] for r in sortie["references"]], ["7", "15"])

    def test_code_des_assurances(self):
        sortie, _ = self.lancer({**CLAIM, "conditions_particulieres": CP}, reponse("couvert", cites=("7", "L113-2")))
        self.assertEqual(sortie["references"][1]["source"], "Code des assurances")
        self.assertEqual(sortie["references"][1]["section"], "Article L113-2 — Obligations de l'assuré")

    def test_sans_article_cite(self):
        sortie, _ = self.lancer({**CLAIM, "conditions_particulieres": CP}, reponse("indetermine", cites=()))
        self.verifier_format(sortie)
        self.assertEqual(len(sortie["references"]), 3)  # comme le backend : les 3 premiers passages

    def test_conditions_particulieres_manquantes(self):
        sortie, intake = self.lancer(CLAIM, reponse("indetermine", cites=(), confiance="basse"))
        self.verifier_format(sortie)
        self.assertIn(integration.CP_MANQUANTES, sortie["missing_information"])
        self.assertIsNone(intake["conditions_particulieres"])

    def test_qdrant_indisponible(self):
        sortie, _ = self.lancer(CLAIM, erreur=ConnectionError("Qdrant injoignable"))
        self.verifier_format(sortie)
        self.assertEqual(sortie["coverage_status"], "insufficient_information")
        self.assertEqual(sortie["diagnostic_error"], "ConnectionError")
        self.assertIn("Qdrant injoignable", sortie["explanation"])
        self.assertEqual(sortie["references"], [])

    def test_gemini_en_echec(self):
        rep = reponse("indetermine", cites=(), confiance="basse",
                      justification="Analyse impossible : appel Gemini en échec (HTTP 503).")
        rep["trace"]["articles_fournis"] = FOURNIS
        sortie, _ = self.lancer({**CLAIM, "conditions_particulieres": CP}, rep)
        self.verifier_format(sortie)
        self.assertEqual(sortie["coverage_status"], "insufficient_information")
        self.assertEqual(sortie["diagnostic_error"], "GeminiError")
        self.assertIn("HTTP 503", sortie["explanation"])

    def test_import_impossible(self):
        with mock.patch.dict(sys.modules, {"policy_agent": None, "retriever": None}):  # import → ImportError
            sortie = integration.policy_agent_pour_backend(CLAIM)
        self.verifier_format(sortie)
        self.assertEqual(sortie["diagnostic_error"], "ModuleNotFoundError")

    def test_modele_si_import_impossible(self):
        env = {"LLM_PROVIDER": "ollama", "OLLAMA_POLICY_MODEL": "qwen2.5:3b", "GEMINI_MODEL": "gemini-x"}
        with mock.patch.dict(sys.modules, {"policy_agent": None, "retriever": None}), \
                mock.patch.dict(os.environ, env):
            self.assertEqual(integration.policy_agent_pour_backend(CLAIM)["model"], "qwen2.5:3b")
            os.environ["LLM_PROVIDER"] = "gemini"
            self.assertEqual(integration.policy_agent_pour_backend(CLAIM)["model"], "gemini-x")

    def test_date_en_texte(self):
        _, intake = self.lancer({**CLAIM, "incident_date": "2026-10-03"}, reponse("couvert"))
        self.assertEqual(intake["date_sinistre"], "2026-10-03")


if __name__ == "__main__":
    unittest.main()
