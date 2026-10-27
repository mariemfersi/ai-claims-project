"""Tests du fournisseur LLM configurable de policy_agent.py (LLM_PROVIDER = gemini ou ollama).

Usage :
    python rag/test_llm_provider.py

Aucun appel réseau sortant : Gemini est servi depuis un cache temporaire (urlopen bloqué),
Ollama par un serveur HTTP simulé sur 127.0.0.1. Aucun Qdrant : la recherche est simulée.
"""
import hashlib, json, os, sys, tempfile, threading, types, unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import policy_agent as pa
import integration

REPONSE_P4 = {"garantie_applicable": {"nom": "dommages collision", "article": "7"}, "exclusions_applicables": [],
              "franchise": {"montant": "300 euros", "article": "20", "detail": "franchise fixe"},
              "verdict_couverture": "couvert", "articles_cites": ["7", "20"],
              "justification": "La garantie dommages collision est souscrite (conditions particulières) (7).",
              "confiance": "haute"}
FOURNIS = [{"article": "7", "titre": "Dommages collision", "source": "contrat", "score": 0.05, "questions": [1],
            "texte": "Article 7. Collision avec un tiers identifié.", "meilleur_chunk": "Article 7.", "nb_chunks": 1},
           {"article": "20", "titre": "Tableau des franchises", "source": "contrat", "score": 0.04, "questions": [3],
            "texte": "Article 20. Franchise de 300 euros.", "meilleur_chunk": "Article 20.", "nb_chunks": 1}]
CLAIM = {"customer_name": "Sami Ben Ali", "policy_number": "AUTO-1", "incident_date": "2026-10-03",
         "location": "Tunis", "description": "Percuté à l'arrière par une autre voiture au feu rouge.",
         "conditions_particulieres": {"garanties": ["responsabilite_civile", "dommages_collision"]}}


class FauxOllama(BaseHTTPRequestHandler):
    """Répond comme /v1/chat/completions d'Ollama et garde chaque requête reçue."""
    requetes, contenu = [], json.dumps(REPONSE_P4)

    def do_POST(self):
        corps = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FauxOllama.requetes.append({"path": self.path, "headers": dict(self.headers), "body": corps})
        reponse = json.dumps({"choices": [{"message": {"role": "assistant", "content": FauxOllama.contenu}}]})
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(reponse.encode())

    def log_message(self, *args):
        pass


def bloque(*args, **kwargs):
    raise AssertionError("appel réseau inattendu")


class BaseTest(unittest.TestCase):
    env = {}

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        patches = [mock.patch.object(pa, "CACHE_DIR", Path(self.tmp.name)),
                   mock.patch.dict(os.environ, self.env, clear=False)]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        for var in ("LLM_PROVIDER", "GEMINI_API_KEY", "GEMINI_MODEL", "GEMINI_REASONING_EFFORT",
                    "OLLAMA_BASE_URL", "OLLAMA_POLICY_MODEL"):
            if var not in self.env:
                os.environ.pop(var, None)
        self.addCleanup(self.tmp.cleanup)


class TestGeminiCache(BaseTest):
    def test_cle_inchangee(self):
        # même formule qu'avant l'ajout du fournisseur : les réponses Gemini déjà en cache restent valides
        p = pa._params("S", "U", pa.SCHEMA_P4)
        ancienne = json.dumps({k: p.get(k) for k in ("model", "reasoning_effort", "temperature", "response_format",
                                                     "messages")}, ensure_ascii=False, sort_keys=True)
        self.assertEqual(pa.cache_path("S", "U", pa.SCHEMA_P4).name,
                         f"{hashlib.sha256(ancienne.encode()).hexdigest()}.json")
        self.assertEqual(p["reasoning_effort"], "low")
        self.assertEqual(p["model"], pa.DEFAULT_MODEL)

    def test_depuis_le_cache_sans_reseau(self):
        fichier = pa.cache_path(pa.PROMPT_P4, "U", pa.SCHEMA_P4)
        fichier.write_text(json.dumps({"content": json.dumps(REPONSE_P4)}), encoding="utf-8")
        journal = []
        with mock.patch("urllib.request.urlopen", bloque):  # GEMINI_API_KEY non défini, et aucun appel
            texte = pa.call_gemini(pa.PROMPT_P4, "U", "p4", journal, schema=pa.SCHEMA_P4)
        self.assertEqual(json.loads(texte), REPONSE_P4)
        self.assertEqual(journal[0]["statut"], "cache")

    def test_analyse_depuis_le_cache(self):
        intake = integration.intake_depuis_claim(CLAIM)
        with mock.patch.object(pa, "retrouver_articles", lambda qs: [dict(a) for a in FOURNIS]):
            user, _ = pa.prompt_p4(intake, FOURNIS)
            pa.cache_path(pa.PROMPT_P4, user, pa.SCHEMA_P4).write_text(
                json.dumps({"content": json.dumps(REPONSE_P4)}), encoding="utf-8")
            with mock.patch("urllib.request.urlopen", bloque):
                rep = pa.analyse_couverture(intake)
        self.assertEqual(rep["verdict_couverture"], "couvert")
        self.assertEqual(rep["trace"]["fournisseur"], "gemini")
        self.assertEqual(rep["trace"]["appels"][0]["statut"], "cache")

    def test_sans_cle(self):
        with self.assertRaisesRegex(pa.GeminiError, "GEMINI_API_KEY"):
            pa.call_gemini("S", "U", cache=False)


class TestOllama(BaseTest):
    env = {"LLM_PROVIDER": "ollama", "OLLAMA_POLICY_MODEL": "qwen2.5:3b", "GEMINI_API_KEY": "cle-secrete"}

    @classmethod
    def setUpClass(cls):
        cls.serveur = HTTPServer(("127.0.0.1", 0), FauxOllama)
        threading.Thread(target=cls.serveur.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()

    def setUp(self):
        self.env = {**self.env, "OLLAMA_BASE_URL": f"http://127.0.0.1:{self.serveur.server_port}"}
        super().setUp()
        FauxOllama.requetes.clear()
        FauxOllama.contenu = json.dumps(REPONSE_P4)

    def test_requete(self):
        texte = pa.call_gemini(pa.PROMPT_P4, "U", "p4", schema=pa.SCHEMA_P4)
        self.assertEqual(json.loads(texte), REPONSE_P4)
        req = FauxOllama.requetes[0]
        self.assertEqual(req["path"], "/v1/chat/completions")
        self.assertNotIn("Authorization", req["headers"])          # pas de clé API envoyée
        self.assertNotIn("reasoning_effort", req["body"])
        self.assertEqual(req["body"]["model"], "qwen2.5:3b")
        self.assertEqual(req["body"]["temperature"], 0)
        self.assertEqual(req["body"]["response_format"]["type"], "json_schema")
        self.assertEqual(req["body"]["response_format"]["json_schema"]["schema"], pa.SCHEMA_P4)

    def test_url_avec_v1(self):
        os.environ["OLLAMA_BASE_URL"] += "/v1/"
        pa.call_gemini("S", "U", cache=False)
        self.assertEqual(FauxOllama.requetes[0]["path"], "/v1/chat/completions")

    def test_cache(self):
        cle_ollama = pa.cache_path("S", "U")
        pa.call_gemini("S", "U")
        pa.call_gemini("S", "U")  # 2e appel : depuis le cache
        self.assertEqual(len(FauxOllama.requetes), 1)
        self.assertEqual(json.loads(cle_ollama.read_text(encoding="utf-8"))["fournisseur"], "ollama")
        os.environ["OLLAMA_POLICY_MODEL"] = "qwen2.5:7b"
        self.assertNotEqual(pa.cache_path("S", "U"), cle_ollama)   # le modèle est dans la clé
        os.environ["LLM_PROVIDER"] = "gemini"
        os.environ["GEMINI_MODEL"] = "qwen2.5:3b"
        os.environ["GEMINI_REASONING_EFFORT"] = ""
        self.assertNotEqual(pa.cache_path("S", "U"), cle_ollama)   # le fournisseur aussi

    def test_json_invalide(self):
        FauxOllama.contenu = "pas du JSON"
        intake = integration.intake_depuis_claim(CLAIM)
        with mock.patch.object(pa, "retrouver_articles", lambda qs: [dict(a) for a in FOURNIS]):
            rep = pa.analyse_couverture(intake)
        self.assertEqual(rep["verdict_couverture"], "indetermine")
        self.assertIn("Réponse P4 : JSON invalide ou incomplet.", rep["trace"]["avertissements"])

    def test_serveur_arrete(self):
        os.environ["OLLAMA_BASE_URL"] = "http://127.0.0.1:9"  # port fermé
        with mock.patch.object(pa, "backoff", lambda attempt: 0):
            with self.assertRaisesRegex(pa.GeminiError, "échec après"):
                pa.call_gemini("S", "U", cache=False)

    def test_integration_sans_changement(self):
        retriever = types.SimpleNamespace(_state={"model_name": "BAAI/bge-m3", "chunks": [
            {"text": a["texte"], "metadata": {"article": a["article"]}} for a in FOURNIS]})
        with mock.patch.object(pa, "retrouver_articles", lambda qs: [dict(a) for a in FOURNIS]), \
                mock.patch.dict(sys.modules, {"retriever": retriever}):
            sortie = integration.policy_agent_pour_backend(CLAIM)
        self.assertEqual(sortie["coverage_status"], "covered")
        self.assertEqual(sortie["model"], "qwen2.5:3b")
        self.assertEqual(sortie["trace"]["fournisseur"], "ollama")
        self.assertIsNone(sortie["trace"]["reasoning_effort"])
        self.assertEqual([r["article"] for r in sortie["references"]], ["7", "20"])
        self.assertIsNone(sortie["diagnostic_error"])


class TestModeleSurErreur(BaseTest):
    """integration : model est celui du fournisseur actif même si l'analyse échoue avant l'appel au LLM."""

    def lancer(self):
        def qdrant_indisponible(qs):
            raise ConnectionError("Qdrant injoignable")
        with mock.patch.object(pa, "retrouver_articles", qdrant_indisponible), \
                mock.patch.dict(sys.modules, {"retriever": None}):
            return integration.policy_agent_pour_backend(CLAIM)

    def test_ollama(self):
        os.environ.update(LLM_PROVIDER="ollama", OLLAMA_POLICY_MODEL="qwen2.5:7b", GEMINI_MODEL="gemini-x")
        sortie = self.lancer()
        self.assertEqual(sortie["diagnostic_error"], "ConnectionError")
        self.assertEqual(sortie["model"], "qwen2.5:7b")

    def test_ollama_modele_par_defaut(self):
        os.environ["LLM_PROVIDER"] = "ollama"
        self.assertEqual(self.lancer()["model"], pa.OLLAMA_DEFAULT_MODEL)

    def test_gemini(self):
        sortie = self.lancer()
        self.assertEqual(sortie["diagnostic_error"], "ConnectionError")
        self.assertEqual(sortie["model"], pa.DEFAULT_MODEL)


class TestFournisseurInconnu(BaseTest):
    env = {"LLM_PROVIDER": "openai"}

    def test_indetermine(self):
        rep = pa.analyse_couverture(integration.intake_depuis_claim(CLAIM))
        self.assertEqual(rep["verdict_couverture"], "indetermine")
        self.assertIn("LLM_PROVIDER inconnu", rep["justification"])


if __name__ == "__main__":
    unittest.main()
