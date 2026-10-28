import base64
import difflib
import json
import math
import mimetypes
import re
import threading
import unicodedata
from functools import lru_cache
from pathlib import Path

import requests
from django.conf import settings
from pydantic import BaseModel, Field


POLICY_CORPUS_PATH = Path(__file__).with_name("policy_corpus.json")
with POLICY_CORPUS_PATH.open(encoding="utf-8") as corpus_file:
    POLICY_CORPUS = json.load(corpus_file)
POLICY_PDF_PATH = Path(__file__).parent / "corpus" / "axa_mon_auto_septembre_2026.pdf"
_OLLAMA_REQUEST_LOCK = threading.Lock()


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
    visible_damage: bool = False
    damaged_areas: list[str] = Field(default_factory=list)
    damage_types: list[str] = Field(default_factory=list)
    severity: str = "unknown"
    image_quality: str = "unknown"
    observations: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)


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


def _ollama_post(path, payload, timeout):
    # Keep a single local inference active at a time to avoid model swaps/timeouts
    # on machines whose VRAM/RAM cannot hold Qwen and LLaVA concurrently.
    with _OLLAMA_REQUEST_LOCK:
        response = requests.post(
            f"{settings.OLLAMA_BASE_URL}{path}",
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        return response


def _parse_json_content(content):
    """Accept JSON returned bare, inside a Markdown fence, or with a short preamble."""
    text = str(content or "").strip()
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 3:
            text = parts[1].strip()
            if text.lower().startswith("json"):
                text = text[4:].lstrip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("La réponse Ollama ne contient pas d'objet JSON.")
    return json.loads(text[start:end + 1])


def _parse(kind, schema, system_prompt, content, images=None):
    model = _model(kind)
    user_message = {"role": "user", "content": content}
    if images:
        user_message["images"] = [data for _, data in images]
    response = _ollama_post(
        "/api/chat",
        {
            "model": model,
            "messages": [{"role": "system", "content": system_prompt}, user_message],
            "stream": False,
            "format": "json" if schema is VisionAnalysis else schema.model_json_schema(),
            "options": {"temperature": 0, **({"num_predict": 256} if schema is VisionAnalysis else {})},
        },
        settings.AI_REQUEST_TIMEOUT,
    )
    payload = _parse_json_content(response.json()["message"]["content"])
    if schema is PolicyAnalysis:
        payload = _normalize_policy_payload(payload)
    return schema.model_validate(payload).model_dump()


def _normalize_policy_payload(payload):
    """Normalise les petites variations JSON produites par les modèles Ollama locaux."""
    if not isinstance(payload, dict):
        payload = {}
    raw_status = str(payload.get("coverage_status", "insufficient_information")).lower().strip()
    status_aliases = {
        "couvert": "covered", "couverte": "covered", "garanti": "covered",
        "exclu": "excluded", "exclue": "excluded", "non couvert": "excluded",
        "inconnu": "insufficient_information", "indéterminé": "insufficient_information",
        "unknown": "insufficient_information", "insufficient": "insufficient_information",
    }
    status = status_aliases.get(raw_status, raw_status)
    if status not in {"covered", "excluded", "insufficient_information"}:
        status = "insufficient_information"

    articles = payload.get("applicable_articles") or []
    if isinstance(articles, (str, int)):
        articles = [articles]
    normalized_articles = []
    for article in articles if isinstance(articles, list) else []:
        if isinstance(article, dict):
            page = article.get("page") or article.get("article") or article.get("reference")
            article = f"Page {page}" if page is not None else ""
        if str(article).strip():
            normalized_articles.append(str(article).strip())

    missing = payload.get("missing_information") or []
    if isinstance(missing, str):
        missing = [missing]
    confidence = payload.get("confidence", 0.25)
    try:
        confidence = float(confidence)
        if confidence > 1:
            confidence /= 100
    except (TypeError, ValueError):
        confidence = 0.25
    explanation = payload.get("explanation") or "La couverture ne peut pas être confirmée avec les éléments disponibles."
    if isinstance(explanation, list):
        explanation = " ".join(str(item) for item in explanation)
    return {
        "coverage_status": status,
        "applicable_articles": normalized_articles,
        "explanation": str(explanation),
        "missing_information": [str(item) for item in missing] if isinstance(missing, list) else [],
        "confidence": max(0.0, min(1.0, confidence)),
    }


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


def _compare_pdf_texts(pypdf_text, ocr_text, pages, pypdf_error=None, ocr_error=None):
    normalize = lambda value: " ".join((value or "").casefold().split())
    left, right = normalize(pypdf_text), normalize(ocr_text)
    matcher = difflib.SequenceMatcher(None, left[:12000], right[:12000]) if left and right else None
    similarity = round(matcher.ratio(), 4) if matcher else None
    shared_text = " ".join(
        left[block.a:block.a + block.size].strip()
        for block in (matcher.get_matching_blocks() if matcher else [])
        if block.size >= 20
    )[:1200]
    selected_method = "pypdf" if len(left) >= 80 else ("ocr" if len(right) > len(left) else "pypdf")
    return {
        "status": "compared" if not pypdf_error and not ocr_error else "partial",
        "pages": pages,
        "pypdf_characters": len(pypdf_text),
        "ocr_characters": len(ocr_text),
        "similarity": similarity,
        "shared_text": shared_text,
        "selected_method": selected_method,
        "pypdf_excerpt": pypdf_text[:1200],
        "ocr_excerpt": ocr_text[:1200],
        "error": ocr_error,
        "pypdf_error": pypdf_error,
    }


@lru_cache(maxsize=128)
def _extract_pdf_both_path(path, modified_ns, file_size):
    """Extract PDF text with pypdf and Tesseract OCR, compare both, and select a usable version."""
    from pypdf import PdfReader

    pypdf_error = None
    try:
        reader = PdfReader(path)
        pypdf_text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
        page_count = len(reader.pages)
    except Exception:
        pypdf_text = ""
        page_count = 0
        pypdf_error = "Extraction pypdf impossible"
    ocr_pages = []
    ocr_error = None
    try:
        import pymupdf
        import pytesseract
        from PIL import Image

        pdf = pymupdf.open(path)
        page_count = max(page_count, len(pdf))
        for page in pdf:
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            ocr_pages.append(pytesseract.image_to_string(image, lang="fra+eng", config="--psm 3"))
        pdf.close()
        ocr_text = "\n".join(ocr_pages).strip()
    except Exception as exc:
        ocr_text = ""
        ocr_error = f"{type(exc).__name__}: OCR indisponible ou en échec"

    # Prefer native extraction for digital PDFs; OCR is the fallback for scans or near-empty layers.
    comparison = _compare_pdf_texts(pypdf_text, ocr_text, page_count, pypdf_error, ocr_error)
    selected_method = comparison["selected_method"]
    selected_text = pypdf_text if selected_method == "pypdf" else ocr_text
    return {
        "text": selected_text,
        "comparison": comparison,
    }


def _extract_pdf_both(document):
    path = document.file.path
    stat = Path(path).stat()
    return _extract_pdf_both_path(path, stat.st_mtime_ns, stat.st_size)


def _read_document_with_comparison(document):
    try:
        path = document.file.path
        if document.mime_type == "application/pdf" or path.lower().endswith(".pdf"):
            return _extract_pdf_both(document)
        return {"text": _read_document(document), "comparison": None}
    except Exception:
        return {"text": "", "comparison": None}


def _has_contract_specific_conditions(claim):
    """Only treat a client document as policy evidence when its filename identifies it as such."""
    markers = ("conditions particulieres", "conditions-particulieres", "conditions_particulieres",
               "contrat", "police assurance", "police_assurance")
    for document in claim.documents.all():
        name = document.original_name.lower()
        if any(marker in name for marker in markers) and _read_document_with_comparison(document)["text"].strip():
            return True
    return False


def _contract_specific_text(claim):
    parts = []
    markers = ("conditions particulieres", "conditions-particulieres", "conditions_particulieres",
               "contrat", "police assurance", "police_assurance")
    for document in claim.documents.all():
        if any(marker in document.original_name.lower() for marker in markers):
            text = _read_document_with_comparison(document)["text"]
            if text.strip():
                parts.append(f"[Pièce client : {document.original_name}]\n{text[:30000]}")
    return "\n\n".join(parts)


def _explicit_collision_coverage(contract_text, policy_number):
    """Return true only when the client policy explicitly confirms active collision cover."""
    if not contract_text or not policy_number:
        return False
    normalized = unicodedata.normalize("NFKD", contract_text.lower())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = " ".join(normalized.replace("\u2019", "'").split())
    if policy_number.lower() not in contract_text.lower():
        return False
    has_collision_cover = bool(re.search(
        r"collision.{0,100}(?:souscrite|active|en vigueur|incluse)|"
        r"(?:souscrite|active|en vigueur|incluse).{0,100}collision|"
        r"dommages tous accidents.{0,100}(?:souscrits|active|en vigueur|inclus)",
        normalized,
    ))
    denies_cover = any(term in normalized for term in (
        "collision non souscrite", "garantie collision non souscrite",
        "collision non garantie", "garantie collision inactive",
        "dommages collision non souscrits",
    ))
    return has_collision_cover and not denies_cover


@lru_cache(maxsize=1)
def _whisper_model():
    from faster_whisper import WhisperModel
    return WhisperModel(
        settings.WHISPER_MODEL,
        device=settings.WHISPER_DEVICE,
        compute_type=settings.WHISPER_COMPUTE_TYPE,
        download_root=settings.WHISPER_MODEL_CACHE,
    )


def _transcribe_audio(document):
    segments, info = _whisper_model().transcribe(
        document.file.path,
        language=settings.WHISPER_LANGUAGE,
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=False,
    )
    text = " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()
    return {
        "file": document.original_name,
        "text": text,
        "language": info.language,
        "language_probability": round(float(info.language_probability), 4),
        "duration_seconds": round(float(info.duration), 2),
        "engine": "faster-whisper",
        "model": settings.WHISPER_MODEL,
    }


def document_agent(claim):
    documents = list(claim.documents.all())
    metadata = []
    extracted_texts = {}
    pdf_comparisons = []
    for document in documents:
        item = {"kind": document.kind, "original_name": document.original_name, "mime_type": document.mime_type}
        if document.kind not in {"PHOTO", "AUDIO"}:
            extraction = _read_document_with_comparison(document)
            extracted_texts[document.id] = extraction["text"]
            if extraction["comparison"]:
                item["pdf_extraction_comparison"] = extraction["comparison"]
                pdf_comparisons.append({"file": document.original_name, **extraction["comparison"]})
        metadata.append(item)
    audio_transcriptions = []
    extraction_errors = []
    if settings.WHISPER_ENABLED:
        for document in (d for d in documents if d.kind == "AUDIO"):
            try:
                audio_transcriptions.append(_transcribe_audio(document))
            except Exception as exc:
                extraction_errors.append(f"Audio {document.original_name}: {type(exc).__name__}")
    facts = {
        "incident_date": claim.incident_date.isoformat(), "location": claim.location,
        "description": claim.description, "policy_number": claim.policy_number,
        "vehicle_registration": None, "parties": [], "declared_amount": None,
        "missing_documents": [] if documents else ["supporting_document"],
        "extraction_notes": extraction_errors or ["Fallback déterministe: Ollama désactivé ou indisponible."],
    }
    engine = "local-fallback"
    if _provider_enabled():
        texts = [f"--- {d.kind}: {d.original_name} ---\n{extracted_texts.get(d.id, '')}" for d in documents if d.kind not in {"PHOTO", "AUDIO"}]
        texts.extend(f"--- AUDIO TRANSCRIT: {item['file']} ---\n{item['text']}" for item in audio_transcriptions)
        prompt = f"FORMULAIRE\nDate: {claim.incident_date}\nLieu: {claim.location}\nPolice: {claim.policy_number}\nDéclaration: {claim.description}\n\nDOCUMENTS\n" + ("\n".join(texts) or "Aucun texte extractible")
        try:
            facts = _parse("document", DocumentFacts, "Extrais les faits du sinistre. N'invente rien; utilise null ou une liste vide si une donnée manque.", prompt)
            facts["extraction_notes"].extend(extraction_errors)
            engine = "ollama"
        except Exception as exc:
            facts["extraction_notes"] = [f"Fallback local: {type(exc).__name__} lors de l'appel Ollama."]
    return {"agent": "document", "engine": engine, "model": _model("document") if engine != "local-fallback" else None, "speech_to_text": {"engine": "faster-whisper", "model": settings.WHISPER_MODEL, "enabled": settings.WHISPER_ENABLED}, "audio_transcriptions": audio_transcriptions, "claim_facts": {k: v for k, v in facts.items() if k not in {"missing_documents", "extraction_notes"}}, "documents": metadata, "pdf_extraction_comparison": pdf_comparisons, "missing_documents": facts["missing_documents"], "extraction_notes": facts["extraction_notes"]}


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
    analysis = {"visible_damage": False, "damaged_areas": [], "damage_types": [], "severity": "unknown", "image_quality": "not_analyzed" if photos else "missing", "observations": ["Photos présentes mais non analysées par le modèle visuel."], "confidence": 0.0}
    engine = "local-fallback"
    diagnostic_error = None
    if _provider_enabled() and docs:
        try:
            system_prompt = "Tu observes des photos de véhicule. Décris seulement ce qui est visible, sans déduire les parties hors champ. Réponds en JSON."
            vision_prompt = (
                "Decris ce qui est visiblement endommage sur ces photos. Indique seulement les zones du vehicule que tu peux voir: "
                "rear, front, left ou right. JSON seulement: {\"damaged_areas\":[]}. "
                "Ne devine pas les parties hors champ."
            )
            analysis = _parse("vision", VisionAnalysis, system_prompt, vision_prompt, _image_content(docs))
            analysis = _normalize_vision_analysis(analysis)
            engine = "ollama"
            if _vision_conflicts_with_photo_labels(docs, analysis["damaged_areas"]):
                diagnostic_error = "PhotoViewConflict"
                analysis["observations"].append(
                    "Analyse visuelle incohérente avec le point de vue indiqué sur le nom d'une photo; vérification requise."
                )
        except Exception as exc:
            analysis["observations"] = [f"Fallback local: {type(exc).__name__} lors de l'appel Ollama."]
            diagnostic_error = type(exc).__name__
    return {"agent": "vision", "engine": engine, "model": _model("vision") if engine != "local-fallback" else None, "photos": photos, "analysis_status": "complete" if engine == "ollama" and diagnostic_error is None else "incomplete", "diagnostic_error": diagnostic_error, **analysis}


def _vision_conflicts_with_photo_labels(documents, damaged_areas):
    areas = set(damaged_areas)
    for document in documents:
        name = document.original_name.lower().replace("é", "e").replace("è", "e")
        if any(marker in name for marker in ("vue_arriere", "vue-arriere", "vue arriere", "rear_view")) and "front" in areas:
            return True
        if any(marker in name for marker in ("vue_avant", "vue-avant", "vue avant", "front_view")) and "rear" in areas:
            return True
    return False


def _normalize_vision_analysis(analysis):
    observations = " ".join(str(item) for item in analysis.get("observations", [])).lower()
    areas = [str(area).lower().strip() for area in analysis.get("damaged_areas", []) if str(area).strip()]
    aliases = {
        "arrière": "rear", "pare-chocs arrière": "rear", "coffre": "rear",
        "avant": "front", "gauche": "left", "droite": "right",
    }
    areas = [aliases.get(area, area) for area in areas]
    if analysis.get("visible_damage") and not areas:
        if any(term in observations for term in ("rear", "trunk", "taillight", "arrière", "coffre")):
            areas.append("rear")
        elif any(term in observations for term in ("front", "hood", "headlight", "avant", "capot")):
            areas.append("front")
    analysis["damaged_areas"] = list(dict.fromkeys(areas))
    if analysis["damaged_areas"]:
        analysis["visible_damage"] = True
    analysis["observations"] = []
    analysis["damage_types"] = []
    return analysis


def _cosine(a, b):
    denominator = math.sqrt(sum(x*x for x in a)) * math.sqrt(sum(x*x for x in b))
    return sum(x*y for x, y in zip(a, b)) / denominator if denominator else 0.0


@lru_cache(maxsize=128)
def _embedding(text):
    response = _ollama_post(
        "/api/embed",
        {"model": _model("embedding"), "input": text},
        settings.AI_REQUEST_TIMEOUT,
    )
    return tuple(response.json()["embeddings"][0])


@lru_cache(maxsize=1)
def _policy_chunks():
    from pypdf import PdfReader
    reader = PdfReader(POLICY_PDF_PATH)
    first_page = POLICY_CORPUS["indexed_pdf_pages"]["from"]
    last_page = POLICY_CORPUS["indexed_pdf_pages"]["to"]
    chunks = []
    for page_number in range(first_page, last_page + 1):
        text = "\n".join(line.strip() for line in (reader.pages[page_number - 1].extract_text() or "").splitlines() if line.strip())
        if len(text) < 80:
            continue
        chunks.append({
            "chunk_id": f"axa-mon-auto-2026-p{page_number}",
            "page": page_number,
            "section": next((line for line in text.splitlines()[1:8] if len(line) > 8), "Conditions générales Mon Auto"),
            "text": text[:12000],
            "source": POLICY_CORPUS["title"],
            "insurer": POLICY_CORPUS["insurer"],
            "version": POLICY_CORPUS["version"],
            "source_url": POLICY_CORPUS["source_url"],
        })
    return chunks


@lru_cache(maxsize=1)
def _policy_chunk_embeddings():
    chunks = _policy_chunks()
    response = _ollama_post(
        "/api/embed",
        {"model": _model("embedding"), "input": [chunk["text"] for chunk in chunks]},
        max(settings.AI_REQUEST_TIMEOUT, 600),
    )
    return tuple(tuple(vector) for vector in response.json()["embeddings"])


def _retrieve(query):
    query_vector = _embedding(query)
    ranked = [(_cosine(query_vector, vector), chunk) for vector, chunk in zip(_policy_chunk_embeddings(), _policy_chunks())]
    return [{**chunk, "similarity": round(score, 4)} for score, chunk in sorted(ranked, reverse=True, key=lambda x: x[0])[:5]]


def _local_retrieve(query):
    normalized = query.lower()
    words = set(normalized.replace("'", " ").split())
    ranked = []
    intent_terms = {"accident", "collision", "choc", "dommages", "sinistre", "arrière", "véhicule"}
    for chunk in _policy_chunks():
        chunk_words = set(chunk["text"].lower().replace("'", " ").split())
        lexical = len(words & chunk_words)
        intent = sum(2 for term in intent_terms if term in normalized and term in chunk_words)
        ranked.append((lexical + intent, chunk))
    return [{**chunk, "similarity": None} for score, chunk in sorted(ranked, reverse=True, key=lambda x: x[0])[:5] if score]


def policy_agent(claim):
    query = (
        f"Sinistre automobile: {claim.description}\n"
        "Garanties recherchées: dommages au véhicule, collision, dommages tous accidents, "
        "choc avec un tiers, responsabilité civile et exclusions applicables.\n"
        f"Date: {claim.incident_date}\nLieu: {claim.location}"
    )
    retrieved = _local_retrieve(query)
    selected = retrieved[0] if retrieved else None
    contract_text = _contract_specific_text(claim)
    analysis = {"coverage_status": "insufficient_information", "applicable_articles": [], "explanation": "Des passages contractuels ont été retrouvés, mais le fallback lexical ne décide pas seul de la couverture.", "missing_information": ["Conditions particulières et garanties souscrites"], "confidence": 0.25 if selected else 0.1}
    engine = "local-fallback"
    diagnostic_error = None
    if _provider_enabled():
        try:
            retrieved = _retrieve(query)
            context = "\n\n".join(f"[Page {a['page']} - {a['section']}]\n{a['text']}" for a in retrieved)
            if contract_text:
                context += f"\n\nCONDITIONS PARTICULIÈRES FOURNIES PAR LE CLIENT\n{contract_text}"
            analysis = _parse("policy", PolicyAnalysis, "Vérifie la couverture uniquement avec les extraits contractuels AXA fournis. Cherche en priorité dommages au véhicule, collision et dommages tous accidents. coverage_status: covered uniquement si la garantie souscrite est confirmée dans les Conditions particulières du client; excluded uniquement si une exclusion explicite correspond au sinistre; sinon insufficient_information. Si les Conditions particulières du client sont absentes, réponds obligatoirement insufficient_information. Dans applicable_articles, cite les pages sous la forme 'Page 42'.", f"SINISTRE\n{query}\n\nEXTRAITS CONTRACTUELS\n{context}")
            engine = "ollama-rag"
        except Exception as exc:
            diagnostic_error = type(exc).__name__
    location_and_policy = f"{claim.location} {claim.policy_number}".lower()
    tunisian_case = any(marker in location_and_policy for marker in ("tunis", "tunisie", "-tn", "tn-"))
    if POLICY_CORPUS.get("country") == "France" and tunisian_case:
        analysis["coverage_status"] = "insufficient_information"
        analysis["explanation"] = "Le corpus disponible est un contrat AXA France, alors que le dossier est tunisien. La couverture doit être vérifiée dans le contrat réellement souscrit."
        missing = list(analysis.get("missing_information", []))
        if "Contrat tunisien et Conditions particulières" not in missing:
            missing.append("Contrat tunisien et Conditions particulières")
        analysis["missing_information"] = missing
        analysis["confidence"] = min(analysis.get("confidence", 0.25), 0.45)
    if not contract_text:
        analysis["coverage_status"] = "insufficient_information"
        analysis["explanation"] = "Les Conditions générales AXA retrouvées décrivent les garanties possibles, mais les Conditions particulières du client ne sont pas jointes. La garantie effectivement souscrite ne peut pas être confirmée."
        missing = list(analysis.get("missing_information", []))
        if "Conditions particulières et garanties souscrites" not in missing:
            missing.append("Conditions particulières et garanties souscrites")
        analysis["missing_information"] = missing
        analysis["confidence"] = min(analysis.get("confidence", 0.25), 0.25)
    elif analysis["coverage_status"] == "insufficient_information" and _explicit_collision_coverage(contract_text, claim.policy_number):
        analysis["coverage_status"] = "covered"
        analysis["explanation"] = "Les Conditions particulières du dossier confirment explicitement la garantie dommages collision comme souscrite et active."
        analysis["missing_information"] = [
            item for item in analysis.get("missing_information", [])
            if "garantie" not in item.lower() and "conditions particulières" not in item.lower()
        ]
        analysis["confidence"] = max(analysis.get("confidence", 0.0), 0.9)
    cited_pages = {int(value.lower().replace("page", "").strip()) for value in analysis["applicable_articles"] if value.lower().replace("page", "").strip().isdigit()}
    refs = [chunk for chunk in retrieved if chunk["page"] in cited_pages] or retrieved[:3]
    refs = [{**chunk, "text": chunk["text"][:600].rstrip() + ("…" if len(chunk["text"]) > 600 else "")} for chunk in refs]
    return {"agent": "policy_rag", "engine": engine, "model": _model("policy") if engine != "local-fallback" else None, "embedding_model": _model("embedding") if engine != "local-fallback" else None, "coverage_status": analysis["coverage_status"], "references": refs, "retrieved_chunks": retrieved, "retrieval_query": query, "explanation": analysis["explanation"], "missing_information": analysis["missing_information"], "confidence": analysis["confidence"], "diagnostic_error": diagnostic_error}


def fraud_agent(document_result, vision_result, policy_result):
    inconsistencies = []
    vision_incomplete = vision_result.get("analysis_status") == "incomplete" or vision_result.get("engine") == "local-fallback"
    description = document_result["claim_facts"]["description"].lower()
    declared_areas = set()
    if any(term in description for term in ("arrière", "arriere", "rear", "coffre")):
        declared_areas.add("rear")
    if any(term in description for term in ("frontal", "avant", "front", "capot")):
        declared_areas.add("front")
    visual_areas = set()
    for area in vision_result.get("damaged_areas", []):
        normalized = str(area).lower()
        if any(term in normalized for term in ("rear", "arrière", "arriere")):
            visual_areas.add("rear")
        if any(term in normalized for term in ("front", "avant")):
            visual_areas.add("front")
    if not vision_incomplete and declared_areas and visual_areas and declared_areas.isdisjoint(visual_areas):
        inconsistencies.append({"type": "damage_location_mismatch", "severity": "high", "points": 50, "evidence": f"La déclaration situe le choc à {', '.join(sorted(declared_areas))}, mais l'analyse visuelle situe les dommages à {', '.join(sorted(visual_areas))}."})
    if document_result.get("missing_documents"):
        inconsistencies.append({"type": "missing_document", "severity": "medium", "points": 25, "evidence": "Une pièce justificative requise n'a pas été fournie."})
    risk = min(100, sum(x["points"] for x in inconsistencies))
    if vision_incomplete:
        if vision_result.get("diagnostic_error") == "PhotoViewConflict":
            evidence = "Le VLM a indiqué une zone incompatible avec le point de vue d'une photo; cette sortie n'est pas validée et n'est pas comptée comme incohérence."
        else:
            evidence = "L'analyse des photos n'est pas validée; la cohérence des zones de dégâts ne peut pas être confirmée."
        inconsistencies.append({"type": "vision_analysis_unavailable", "severity": "unknown", "points": 0, "evidence": evidence})
    return {"agent": "fraud", "assessment_status": "incomplete" if vision_incomplete else "complete", "inconsistencies": inconsistencies, "risk_score": None if vision_incomplete else risk, "observed_risk_score": risk, "score_breakdown": [{"rule": x["type"], "severity": x["severity"], "points": x["points"], "evidence": x["evidence"]} for x in inconsistencies if x["points"]], "formula": "min(100, somme des points observés; score non final si l'analyse visuelle échoue)"}


def decision_agent(document_result, vision_result, policy_result, fraud_result):
    status = policy_result.get("coverage_status")
    risk = fraud_result.get("risk_score")
    observed_risk = fraud_result.get("observed_risk_score", risk or 0)
    risk_for_rules = risk if risk is not None else observed_risk
    fraud_incomplete = fraud_result.get("assessment_status") == "incomplete"
    penalties = []
    if document_result.get("missing_documents"): penalties.append({"reason": "Pièce justificative manquante", "value": 0.18})
    if not vision_result.get("visible_damage"): penalties.append({"reason": "Aucune photo exploitable", "value": 0.12})
    if status == "insufficient_information": penalties.append({"reason": "Couverture non retrouvée", "value": 0.20})
    if fraud_incomplete and vision_result.get("visible_damage"):
        penalties.append({"reason": "Analyse visuelle incomplète", "value": 0.12})
    if risk_for_rules: penalties.append({"reason": "Risque détecté", "value": round((risk_for_rules / 100) * 0.25, 3)})
    confidence = round(max(0.45, min(0.95, 0.95 - sum(x["value"] for x in penalties))), 3)
    fraud_reasons = [x["evidence"] for x in fraud_result.get("inconsistencies", [])]
    if status == "excluded": decision, reasons = "REJECT", [policy_result.get("explanation", "Une exclusion contractuelle explicite s'applique.")]
    elif status == "insufficient_information" or fraud_incomplete: decision, reasons = "INVESTIGATE", [policy_result.get("explanation", "La couverture ne peut pas être confirmée."), *(["Les Conditions particulières et les garanties souscrites doivent être vérifiées."] if status == "insufficient_information" else []), *fraud_reasons]
    elif risk_for_rules: decision, reasons = "INVESTIGATE", fraud_reasons
    else: decision, reasons = "ACCEPT", ["Une garantie applicable a été retrouvée.", "Aucune incohérence majeure n'a été détectée."]
    return {"agent": "decision", "decision": decision, "confidence": confidence, "risk_score": risk, "observed_risk_score": observed_risk, "reasons": reasons, "policy_references": policy_result.get("references", []), "confidence_breakdown": {"base": 0.95, "penalties": penalties, "formula": "max(0.45, min(0.95, base - somme des pénalités))", "result": confidence}}
