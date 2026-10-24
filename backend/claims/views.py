from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .agents import POLICY_CORPUS, document_agent, vision_agent, policy_agent, fraud_agent, decision_agent
from .models import Claim, ClaimDocument, InsuranceContact
from .serializers import ClaimSerializer, InsuranceContactSerializer
from .services import send_claim_handoff_email, trigger_n8n


@api_view(["GET"])
def system_info(request):
    return Response({
        "automation": {
            "engine": "n8n",
            "mode": "Workflow automatique de bout en bout",
            "trigger": "Webhook appelé par Django après la création d'un dossier",
        },
        "agents": [
            {"key": "document", "name": "Document Agent", "order": 1, "execution": "parallel", "engine": "Faster-Whisper + Ollama + extraction PDF/OCR", "llm": settings.OLLAMA_DOCUMENT_MODEL, "speech_model": settings.WHISPER_MODEL, "status": "Actif avec fallback local", "input": "Formulaire, constat PDF, facture et audio", "output": "Transcription, faits structurés, documents et pièces manquantes"},
            {"key": "vision", "name": "Vision Agent", "order": 1, "execution": "parallel", "engine": "VLM via Ollama", "llm": settings.OLLAMA_VISION_MODEL, "status": "Actif avec fallback local", "input": "Photos du véhicule", "output": "Zone endommagée, sévérité, qualité et cohérence"},
            {"key": "policy", "name": "Policy RAG Agent", "order": 1, "execution": "parallel", "engine": "Embeddings + similarité cosinus + Ollama", "llm": settings.OLLAMA_POLICY_MODEL, "status": "RAG actif avec fallback lexical", "input": "Description du sinistre et corpus de garanties", "output": "Statut de couverture et articles justificatifs"},
            {"key": "fraud", "name": "Fraud Agent", "order": 2, "execution": "sequential", "engine": "Moteur de règles pondérées", "llm": None, "status": "MVP déterministe", "input": "Résultats Document, Vision et Policy RAG", "output": "Incohérences, preuves et score de risque"},
            {"key": "decision", "name": "Decision Agent", "order": 3, "execution": "sequential", "engine": "Règles de décision", "llm": None, "status": "MVP déterministe", "input": "Couverture, pièces, vision et score de risque", "output": "ACCEPT, INVESTIGATE ou REJECT avec confiance"},
        ],
        "rag": {
            "mode": "Corpus local découpé par article",
            "corpus_id": POLICY_CORPUS["corpus_id"],
            "title": POLICY_CORPUS["title"],
            "origin": POLICY_CORPUS["origin"],
            "status": POLICY_CORPUS["status"],
            "version": POLICY_CORPUS["version"],
            "warning": POLICY_CORPUS["warning"],
            "source_file": "backend/claims/policy_corpus.json",
            "contract_pdf": POLICY_CORPUS["source_file"],
            "source_url": POLICY_CORPUS["source_url"],
            "insurer": POLICY_CORPUS["insurer"],
            "country": POLICY_CORPUS["country"],
            "page_count": POLICY_CORPUS["page_count"],
            "indexed_pdf_pages": POLICY_CORPUS["indexed_pdf_pages"],
            "embedding_model": settings.OLLAMA_EMBEDDING_MODEL,
            "vector_store": "Mémoire Python (similarité cosinus)",
            "documents": [{"title": POLICY_CORPUS["title"], "insurer": POLICY_CORPUS["insurer"], "version": POLICY_CORPUS["version"], "pages": POLICY_CORPUS["page_count"], "url": POLICY_CORPUS["source_url"]}],
            "retrieval": "Top 5 pages par similarité sémantique, puis réponse limitée aux passages retrouvés",
            "next_step": "Ajouter les Conditions particulières d'un contrat de démonstration et migrer les vecteurs vers pgvector",
        },
        "risk": {
            "formula": "min(100, somme des points)",
            "weights": {"low": 10, "medium": 25, "high": 50},
            "rules": [
                {"key": "damage_location_mismatch", "label": "Zone des dommages contradictoire", "points": 50},
                {"key": "missing_document", "label": "Pièce justificative manquante", "points": 25},
            ],
        },
        "confidence": {
            "base": 0.95,
            "minimum": 0.45,
            "maximum": 0.95,
            "penalties": [
                {"label": "Pièce justificative manquante", "value": 0.18},
                {"label": "Aucune photo exploitable", "value": 0.12},
                {"label": "Couverture non retrouvée", "value": 0.20},
                {"label": "Risque", "value": "score de risque / 100 × 0.25"},
            ],
        },
    })


class ClaimViewSet(viewsets.ModelViewSet):
    queryset = Claim.objects.select_related("assigned_contact").prefetch_related("documents").order_by("-created_at")
    serializer_class = ClaimSerializer
    http_method_names = ["get", "post"]

    def perform_create(self, serializer):
        claim = serializer.save()
        try:
            trigger_n8n(claim)
        except Exception as exc:
            claim.status = Claim.Status.FAILED
            claim.error_message = f"Impossible de déclencher n8n: {exc}"
            claim.save(update_fields=["status", "error_message", "updated_at"])

    @action(detail=True, methods=["post"])
    def retry(self, request, pk=None):
        claim = self.get_object()
        claim.error_message = ""
        claim.status = Claim.Status.SUBMITTED
        claim.save(update_fields=["status", "error_message", "updated_at"])
        try:
            trigger_n8n(claim)
        except Exception as exc:
            claim.status = Claim.Status.FAILED
            claim.error_message = str(exc)
            claim.save(update_fields=["status", "error_message", "updated_at"])
        return Response(ClaimSerializer(claim, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="handoff")
    def handoff(self, request, pk=None):
        claim = self.get_object()
        if claim.decision != Claim.Decision.INVESTIGATE:
            return Response({"detail": "Seuls les dossiers À examiner peuvent être transmis."}, status=status.HTTP_400_BAD_REQUEST)
        contact = get_object_or_404(InsuranceContact, id=request.data.get("contact_id"), is_active=True)
        claim.assigned_contact = contact
        claim.handoff_at = timezone.now()
        claim.handoff_note = str(request.data.get("note", "")).strip()
        claim.save(update_fields=["assigned_contact", "handoff_at", "handoff_note", "updated_at"])
        _send_handoff_email(claim)
        return Response(ClaimSerializer(claim, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="notify-responsible")
    def notify_responsible(self, request, pk=None):
        claim = self.get_object()
        if not claim.assigned_contact:
            return Response({"detail": "Attribue d’abord ce dossier à un responsable."}, status=status.HTTP_400_BAD_REQUEST)
        _send_handoff_email(claim)
        return Response(ClaimSerializer(claim, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="add-files")
    def add_files(self, request, pk=None):
        claim = self.get_object()
        if claim.status == Claim.Status.PROCESSING:
            return Response({"detail": "Le dossier est déjà en cours d'analyse."}, status=status.HTTP_409_CONFLICT)
        files = request.FILES.getlist("files")
        keep_ids_supplied = "keep_document_ids" in request.data
        keep_ids = {value for value in request.data.getlist("keep_document_ids") if value} if keep_ids_supplied else {
            str(document.id) for document in claim.documents.all()
        }
        current_ids = {str(document.id) for document in claim.documents.all()}
        if not keep_ids.issubset(current_ids):
            return Response({"detail": "Une pièce à conserver n'appartient pas à ce dossier."}, status=status.HTTP_400_BAD_REQUEST)
        if keep_ids == current_ids and not files:
            return Response({"detail": "Aucune modification de pièce n'a été demandée."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            documents_to_delete = claim.documents.exclude(id__in=keep_ids)
            for document in documents_to_delete:
                document.file.delete(save=False)
                document.delete()
            for uploaded in files:
                ClaimDocument.objects.create(
                    claim=claim,
                    kind=ClaimSerializer._kind_from_content_type(uploaded.content_type, uploaded.name),
                    file=uploaded,
                    original_name=uploaded.name,
                    mime_type=uploaded.content_type or "",
                )
            history = claim.agent_results.get("history", []) if isinstance(claim.agent_results, dict) else []
            if claim.decision:
                history.append({
                    "decision": claim.decision,
                    "confidence": claim.confidence,
                    "risk_score": claim.risk_score,
                    "reasons": claim.reasons,
                    "policy_references": claim.policy_references,
                    "completed_at": claim.updated_at.isoformat(),
                })
            claim.status = Claim.Status.SUBMITTED
            claim.decision = ""
            claim.confidence = None
            claim.risk_score = None
            claim.reasons = []
            claim.policy_references = []
            claim.assigned_contact = None
            claim.handoff_at = None
            claim.handoff_note = ""
            claim.handoff_email_status = ""
            claim.handoff_email_sent_at = None
            claim.handoff_email_error = ""
            claim.agent_results = {"history": history}
            claim.error_message = ""
            claim.save()

        try:
            trigger_n8n(claim)
        except Exception as exc:
            claim.status = Claim.Status.FAILED
            claim.error_message = f"Pièces ajoutées, mais impossible de relancer n8n: {exc}"
            claim.save(update_fields=["status", "error_message", "updated_at"])
        claim.refresh_from_db()
        return Response(ClaimSerializer(claim, context={"request": request}).data)


class InsuranceContactViewSet(viewsets.ModelViewSet):
    queryset = InsuranceContact.objects.all()
    serializer_class = InsuranceContactSerializer
    http_method_names = ["get", "post", "patch", "delete"]


def _send_handoff_email(claim):
    result, error, sent_at = send_claim_handoff_email(claim)
    claim.handoff_email_status = result
    claim.handoff_email_error = error
    claim.handoff_email_sent_at = sent_at
    claim.save(update_fields=["handoff_email_status", "handoff_email_error", "handoff_email_sent_at", "updated_at"])


@api_view(["GET"])
def internal_claim(request, claim_id):
    claim = get_object_or_404(Claim.objects.prefetch_related("documents"), id=claim_id)
    return Response(ClaimSerializer(claim, context={"request": request}).data)


@api_view(["POST"])
def run_document_agent(request):
    claim = get_object_or_404(Claim, id=request.data.get("claim_id"))
    result = _execute_agent(claim.id, "document", document_agent, claim)
    return Response(result)


@api_view(["POST"])
def run_vision_agent(request):
    claim = get_object_or_404(Claim, id=request.data.get("claim_id"))
    result = _execute_agent(claim.id, "vision", vision_agent, claim)
    return Response(result)


@api_view(["POST"])
def run_policy_agent(request):
    claim = get_object_or_404(Claim, id=request.data.get("claim_id"))
    result = _execute_agent(claim.id, "policy", policy_agent, claim)
    return Response(result)


@api_view(["POST"])
def run_fraud_agent(request):
    claim_id = request.data.get("claim_id")
    result = _execute_agent(claim_id, "fraud", fraud_agent,
        request.data.get("document", {}),
        request.data.get("vision", {}),
        request.data.get("policy", {}),
    )
    return Response(result)


@api_view(["POST"])
def run_decision_agent(request):
    claim_id = request.data.get("claim_id")
    result = _execute_agent(claim_id, "decision", decision_agent,
        request.data.get("document", {}),
        request.data.get("vision", {}),
        request.data.get("policy", {}),
        request.data.get("fraud", {}),
    )
    return Response(result)


def _execute_agent(claim_id, agent_key, callback, *args):
    _mark_agent(claim_id, agent_key, "RUNNING")
    try:
        result = callback(*args)
    except Exception:
        _mark_agent(claim_id, agent_key, "FAILED")
        raise
    _mark_agent(claim_id, agent_key, "COMPLETED", result)
    return result


def _mark_agent(claim_id, agent_key, agent_status, result=None):
    if not claim_id:
        return
    with transaction.atomic():
        claim = Claim.objects.select_for_update().filter(id=claim_id).first()
        if not claim:
            return
        results = claim.agent_results if isinstance(claim.agent_results, dict) else {}
        timeline = results.setdefault("timeline", {"started_at": timezone.now().isoformat(), "agents": {}})
        agents = timeline.setdefault("agents", {})
        entry = agents.setdefault(agent_key, {"status": "PENDING", "expected_seconds": 60})
        now = timezone.now()
        if agent_status == "RUNNING":
            entry["status"] = "RUNNING"
            entry["started_at"] = now.isoformat()
        else:
            entry["status"] = agent_status
            entry["completed_at"] = now.isoformat()
            if entry.get("started_at"):
                started = datetime.fromisoformat(entry["started_at"])
                entry["elapsed_seconds"] = max(0, round((now - started).total_seconds()))
            if result is not None:
                results[agent_key] = result
        claim.agent_results = results
        claim.save(update_fields=["agent_results", "updated_at"])


@api_view(["POST"])
def complete_claim(request, claim_id):
    if request.headers.get("X-Callback-Token") != settings.N8N_CALLBACK_TOKEN:
        return Response({"detail": "Invalid callback token"}, status=status.HTTP_403_FORBIDDEN)
    claim = get_object_or_404(Claim, id=claim_id)
    decision = request.data.get("decision", request.data)
    claim.status = Claim.Status.COMPLETED
    claim.decision = decision.get("decision", "INVESTIGATE")
    claim.confidence = decision.get("confidence")
    claim.risk_score = decision.get("risk_score")
    claim.reasons = decision.get("reasons", [])
    claim.policy_references = decision.get("policy_references", [])
    history = claim.agent_results.get("history", []) if isinstance(claim.agent_results, dict) else []
    claim.agent_results = request.data.get("agent_results", {})
    if not isinstance(claim.agent_results, dict):
        claim.agent_results = {}
    timeline = claim.agent_results.get("timeline")
    if timeline is None and isinstance(request.data.get("timeline"), dict):
        timeline = request.data["timeline"]
    if timeline is None:
        timeline = Claim.objects.filter(id=claim.id).values_list("agent_results", flat=True).first()
        timeline = timeline.get("timeline", {}) if isinstance(timeline, dict) else {}
    claim.agent_results["timeline"] = timeline
    claim.agent_results["history"] = history
    claim.agent_results["decision"] = decision
    claim.error_message = ""
    claim.save()
    return Response(ClaimSerializer(claim, context={"request": request}).data)

