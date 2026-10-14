import base64
import json
import math
import mimetypes
from functools import lru_cache

import requests
from django.conf import settings
from pydantic import BaseModel, Field


POLICY_ARTICLES = [
    {"article": "Article 12", "topic": "collision", "text": "Les dommages causés au véhicule assuré par une collision sont couverts lorsque la garantie dommages collision est active."},
    {"article": "Article 18", "topic": "délai de déclaration", "text": "Le sinistre doit être déclaré dans un délai maximal de cinq jours ouvrés après sa découverte."},
    {"article": "Article 21", "topic": "bris de glace", "text": "Le pare-brise, les vitres latérales et la lunette arrière sont couverts par la garantie bris de glace, sous déduction de la franchise contractuelle."},
    {"article": "Article 24", "topic": "vol", "text": "La garantie vol exige une déclaration aux autorités et la remise du récépissé de dépôt de plainte."},
    {"article": "Article 27", "topic": "exclusion", "text": "Les dommages intentionnels causés par l'assuré sont exclus de la couverture."},
]


class DocumentFacts(BaseModel):
    incident_date: str
    location: str
    description: str
    policy_number: str
    vehicle_registration: str | None = None
    parties: list[str] = Field(default_factory=list)
    declared_amount: float | None = None
    missing_documents: list[str] = Field(default_factory=list)
    extraction_notes: list[str] = Field(default_factory=list)


class VisionAnalysis(BaseModel):
    visible_damage: bool
    damaged_areas: list[str] = Field(default_factory=list)
    damage_types: list[str] = Field(default_factory=list)
    severity: str
    image_quality: str
    observations: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class PolicyAnalysis(BaseModel):
    coverage_status: str
    applicable_articles: list[str] = Field(default_factory=list)
    explanation: str
    missing_information: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


def _provider_enabled():
    return settings.OLLAMA_ENABLED


def _model(kind):
    return {
        "document": settings.OLLAMA_DOCUMENT_MODEL,
        "vision": settings.OLLAMA_VISION_MODEL,
        "policy": settings.OLLAMA_POLICY_MODEL,
        "embedding": settings.OLLAMA_EMBEDDING_MODEL,
    }[kind]


def _parse(kind, schema, system_prompt, content, images=None):
    model = _model(kind)
    user_message = {"role": "user", "content": content}
    if images:
        user_message["images"] = [data for _, data in images]
    response = requests.post(
        f"{settings.OLLAMA_BASE_URL}/api/chat",
        json={
            "model": model,
            "messages": [{"role": "system", "content": system_prompt}, user_message],
            "stream": False,
            "format": schema.model_json_schema(),
            "options": {"temperature": 0},
        },
        timeout=settings.AI_REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return schema.model_validate(json.loads(response.json()["message"]["content"])).model_dump()


def _read_document(document):
    try:
        path = document.file.path
        if document.mime_type == "application/pdf" or path.lower().endswith(".pdf"):
            from pypdf import PdfReader
            return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)[:30000]
        if document.mime_type.startswith("text/"):
            with open(path, encoding="utf-8", errors="ignore") as stream:
                return stream.read(30000)
    except (OSError, ValueError):
        pass
    return ""


def document_agent(claim):
    documents = list(claim.documents.all())
    metadata = [{"kind": d.kind, "original_name": d.original_name, "mime_type": d.mime_type} for d in documents]
    facts = {
        "incident_date": claim.incident_date.isoformat(), "location": claim.location,
        "description": claim.description, "policy_number": claim.policy_number,
        "vehicle_registration": None, "parties": [], "declared_amount": None,
        "missing_documents": [] if documents else ["supporting_document"],
        "extraction_notes": ["Fallback déterministe: Ollama désactivé ou indisponible."],
    }
    engine = "local-fallback"
    if _provider_enabled():
        texts = [f"--- {d.kind}: {d.original_name} ---\n{_read_document(d)}" for d in documents if d.kind != "PHOTO"]
        prompt = f"FORMULAIRE\nDate: {claim.incident_date}\nLieu: {claim.location}\nPolice: {claim.policy_number}\nDéclaration: {claim.description}\n\nDOCUMENTS\n" + ("\n".join(texts) or "Aucun texte extractible")
        try:
            facts = _parse("document", DocumentFacts, "Extrais les faits du sinistre. N'invente rien; utilise null ou une liste vide si une donnée manque.", prompt)
            engine = "ollama"
        except Exception as exc:
            facts["extraction_notes"] = [f"Fallback local: {type(exc).__name__} lors de l'appel Ollama."]
    return {"agent": "document", "engine": engine, "model": _model("document") if engine != "local-fallback" else None, "claim_facts": {k: v for k, v in facts.items() if k not in {"missing_documents", "extraction_notes"}}, "documents": metadata, "missing_documents": facts["missing_documents"], "extraction_notes": facts["extraction_notes"]}


def _image_content(documents):
    content = []
    for document in documents[:6]:
        mime = document.mime_type or mimetypes.guess_type(document.original_name)[0] or "image/jpeg"
        if mime not in {"image/jpeg", "image/png", "image/webp", "image/gif"}:
            continue
        with document.file.open("rb") as stream:
            encoded = base64.b64encode(stream.read()).decode("ascii")
        content.append((mime, encoded))
    return content


def vision_agent(claim):
    docs = list(claim.documents.filter(kind="PHOTO"))
    photos = [d.original_name for d in docs]
    inferred = "rear" if any(x in claim.description.lower() for x in ["arrière", "rear"]) else "front"
    analysis = {"visible_damage": bool(photos), "damaged_areas": [inferred] if photos else [], "damage_types": [], "severity": "medium" if photos else "unknown", "image_quality": "not_analyzed" if photos else "missing", "observations": ["Fallback déterministe: Ollama désactivé ou indisponible."], "confidence": 0.35 if photos else 0.0}
    engine = "local-fallback"
    if _provider_enabled() and docs:
        try:
            analysis = _parse("vision", VisionAnalysis, "Inspecte seulement ce qui est visible. N'identifie personne et ne conclus jamais à une fraude. Lis aussi les textes utiles visibles (OCR). severity: low, medium, high ou unknown.", "Analyse ces photos du véhicule après le sinistre.", _image_content(docs))
            engine = "ollama"
        except Exception as exc:
            analysis["observations"] = [f"Fallback local: {type(exc).__name__} lors de l'appel Ollama."]
    return {"agent": "vision", "engine": engine, "model": _model("vision") if engine != "local-fallback" else None, "photos": photos, **analysis}


def _cosine(a, b):
    denominator = math.sqrt(sum(x*x for x in a)) * math.sqrt(sum(x*x for x in b))
    return sum(x*y for x, y in zip(a, b)) / denominator if denominator else 0.0


@lru_cache(maxsize=128)
def _embedding(text):
    response = requests.post(
        f"{settings.OLLAMA_BASE_URL}/api/embed",
        json={"model": _model("embedding"), "input": text},
        timeout=settings.AI_REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return tuple(response.json()["embeddings"][0])


def _retrieve(query):
    query_vector = _embedding(query)
    ranked = [(_cosine(query_vector, _embedding(f"{a['topic']}\n{a['text']}")), a) for a in POLICY_ARTICLES]
    return [{**article, "similarity": round(score, 4)} for score, article in sorted(ranked, reverse=True, key=lambda x: x[0])[:3]]


def _local_retrieve(query):
    normalized = query.lower()
    words = set(normalized.replace("'", " ").split())
    intent_terms = {
        "collision": {"accident", "collision", "choc", "frontal", "arrière"},
        "délai de déclaration": {"retard", "délai", "jours", "hier"},
        "bris de glace": {"vitre", "pare-brise", "glace"},
        "vol": {"vol", "volé", "dérobé"},
        "exclusion": {"intentionnel", "volontaire"},
    }
    ranked = []
    for article in POLICY_ARTICLES:
        lexical = len(words & set(f"{article['topic']} {article['text']}".lower().split()))
        intent = sum(3 for term in intent_terms[article["topic"]] if term in normalized)
        ranked.append((lexical + intent, article))
    return [{**a, "similarity": None} for score, a in sorted(ranked, reverse=True, key=lambda x: x[0])[:3] if score]


def policy_agent(claim):
    query = f"{claim.description}\nDate: {claim.incident_date}\nLieu: {claim.location}"
    retrieved = _local_retrieve(query)
    selected = retrieved[0] if retrieved else None
    analysis = {"coverage_status": "covered" if selected else "insufficient_information", "applicable_articles": [selected["article"]] if selected else [], "explanation": selected["text"] if selected else "Aucun article pertinent retrouvé.", "missing_information": [], "confidence": 0.45 if selected else 0.2}
    engine = "local-fallback"
    if _provider_enabled():
        try:
            retrieved = _retrieve(query)
            context = "\n\n".join(f"{a['article']} — {a['topic']}\n{a['text']}" for a in retrieved)
            analysis = _parse("policy", PolicyAnalysis, "Vérifie la couverture uniquement avec les articles fournis. coverage_status: covered, excluded ou insufficient_information. Cite les numéros exacts.", f"SINISTRE\n{query}\n\nARTICLES\n{context}")
            engine = "ollama-rag"
        except Exception as exc:
            analysis["explanation"] += f" Fallback local ({type(exc).__name__})."
    refs = [a for a in retrieved if a["article"] in analysis["applicable_articles"]]
    return {"agent": "policy_rag", "engine": engine, "model": _model("policy") if engine != "local-fallback" else None, "embedding_model": _model("embedding") if engine != "local-fallback" else None, "coverage_status": analysis["coverage_status"], "references": refs, "retrieved_chunks": retrieved, "retrieval_query": query, "explanation": analysis["explanation"], "missing_information": analysis["missing_information"], "confidence": analysis["confidence"]}


def fraud_agent(document_result, vision_result, policy_result):
    inconsistencies = []
    description = document_result["claim_facts"]["description"].lower()
    if "frontal" in description and "rear" in vision_result.get("damaged_areas", []):
        inconsistencies.append({"type": "damage_location_mismatch", "severity": "high", "points": 50, "evidence": "La déclaration mentionne un choc frontal, mais l'analyse visuelle indique un dommage arrière."})
    if document_result.get("missing_documents"):
        inconsistencies.append({"type": "missing_document", "severity": "medium", "points": 25, "evidence": "Une pièce justificative requise n'a pas été fournie."})
    risk = min(100, sum(x["points"] for x in inconsistencies))
    return {"agent": "fraud", "inconsistencies": inconsistencies, "risk_score": risk, "score_breakdown": [{"rule": x["type"], "severity": x["severity"], "points": x["points"], "evidence": x["evidence"]} for x in inconsistencies], "formula": "min(100, somme des points: faible=10, moyen=25, élevé=50)"}


def decision_agent(document_result, vision_result, policy_result, fraud_result):
    status, risk = policy_result.get("coverage_status"), fraud_result.get("risk_score", 0)
    penalties = []
    if document_result.get("missing_documents"): penalties.append({"reason": "Pièce justificative manquante", "value": 0.18})
    if not vision_result.get("visible_damage"): penalties.append({"reason": "Aucune photo exploitable", "value": 0.12})
    if status == "insufficient_information": penalties.append({"reason": "Couverture non retrouvée", "value": 0.20})
    if risk: penalties.append({"reason": "Risque détecté", "value": round((risk / 100) * 0.25, 3)})
    confidence = round(max(0.45, min(0.95, 0.95 - sum(x["value"] for x in penalties))), 3)
    if status in {"excluded", "insufficient_information"}: decision, reasons = "REJECT", [policy_result.get("explanation", "Garantie non applicable.")]
    elif risk: decision, reasons = "INVESTIGATE", [x["evidence"] for x in fraud_result.get("inconsistencies", [])]
    else: decision, reasons = "ACCEPT", ["Une garantie applicable a été retrouvée.", "Aucune incohérence majeure n'a été détectée."]
    return {"agent": "decision", "decision": decision, "confidence": confidence, "risk_score": risk, "reasons": reasons, "policy_references": policy_result.get("references", []), "confidence_breakdown": {"base": 0.95, "penalties": penalties, "formula": "max(0.45, min(0.95, base - somme des pénalités))", "result": confidence}}
