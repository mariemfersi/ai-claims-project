"""Envoie un dossier synthétique au webhook n8n.
Usage : python scripts/send_dossier.py D01 [--url http://localhost:5678/webhook-test/claims]
"""
import argparse, json, urllib.request
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("dossier_id")
ap.add_argument("--url", default="http://localhost:5678/webhook-test/claims")
ap.add_argument("--date-depot", default="2026-10-07")
a = ap.parse_args()

data = json.loads((Path(__file__).resolve().parent.parent / "data/dossiers/dossiers_synthetiques.json").read_text(encoding="utf-8"))
d = next(x for x in data["dossiers"] if x["id"] == a.dossier_id)
payload = {k: v for k, v in d.items() if k not in ("attendu", "scenario")}
payload["date_depot"] = a.date_depot
if payload.get("declaration") is None and payload.get("audio"):
    # en attendant Whisper : on simule la transcription
    payload["declaration"] = payload["audio"]["transcription_attendue"]

req = urllib.request.Request(a.url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
print(json.dumps(json.loads(urllib.request.urlopen(req, timeout=60).read()), indent=2, ensure_ascii=False))
