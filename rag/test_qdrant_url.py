"""Test de index_qdrant.get_client : QDRANT_URL choisit le serveur, sinon mode local (qdrant_db/).

Usage :
    python rag/test_qdrant_url.py

Le client Qdrant est simulé : aucun serveur ni dossier qdrant_db/ n'est ouvert.
"""
import os, sys, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import index_qdrant


class TestGetClient(unittest.TestCase):
    def appel(self, env, url=None):
        with mock.patch.dict(os.environ, env, clear=False), mock.patch.object(index_qdrant, "QdrantClient") as qc:
            if "QDRANT_URL" not in env:
                os.environ.pop("QDRANT_URL", None)
            index_qdrant.get_client(url)
        return qc.call_args.kwargs

    def test_local_par_defaut(self):
        self.assertEqual(self.appel({}), {"path": str(index_qdrant.LOCAL_PATH)})

    def test_qdrant_url(self):
        self.assertEqual(self.appel({"QDRANT_URL": "http://qdrant:6333"}), {"url": "http://qdrant:6333"})

    def test_url_explicite_prioritaire(self):
        self.assertEqual(self.appel({"QDRANT_URL": "http://qdrant:6333"}, "http://localhost:6333"),
                         {"url": "http://localhost:6333"})


if __name__ == "__main__":
    unittest.main()
