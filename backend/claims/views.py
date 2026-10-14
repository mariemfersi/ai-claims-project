from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .agents import POLICY_ARTICLES, document_agent, vision_agent, policy_agent, fraud_agent, decision_agent
from .models import Claim
from .serializers import ClaimSerializer
from .services import trigger_n8n


@api_view(["GET"])
def system_info(request):
    return Response({
        "automation": {
            "engine": "n8n",
            "mode": "Workflow automatique de bout en bout",
            "trigger": "Webhook appelé par Django après la création d'un dossier",
        },
        "agents": [
            {"key": "document", "name": "Document Agent", "order": 1, "execution": "parallel", "engine": "Ollama + extraction PDF/OCR", "llm": settings.OLLAMA_DOCUMENT_MODEL, "status": "Actif avec fallback local", "input": "Formulaire, constat PDF et facture", "output": "Faits structurés, documents et pièces manquantes"},
            {"key": "vision", "name": "Vision Agent", "order": 1, "execution": "parallel", "engine": "VLM via Ollama", "llm": settings.OLLAMA_VISION_MODEL, "status": "Actif avec fallback local", "input": "Photos du véhicule", "output": "Zone endommagée, sévérité, qualité et cohérence"},
            {"key": "policy", "name": "Policy RAG Agent", "order": 1, "execution": "parallel", "engine": "Embeddings + similarité cosinus + Ollama", "llm": settings.OLLAMA_POLICY_MODEL, "status": "RAG actif avec fallback lexical", "input": "Description du sinistre et corpus de garanties", "output": "Statut de couverture et articles justificatifs"},
            {"key": "fraud", "name": "Fraud Agent", "order": 2, "execution": "sequential", "engine": "Moteur de règles pondérées", "llm": None, "status": "MVP déterministe", "input": "Résultats Document, Vision et Policy RAG", "output": "Incohérences, preuves et score de risque"},
            {"key": "decision", "name": "Decision Agent", "order": 3, "execution": "sequential", "engine": "Règles de décision", "llm": None, "status": "MVP déterministe", "input": "Couverture, pièces, vision et score de risque", "output": "ACCEPT, INVESTIGATE ou REJECT avec confiance"},
        ],
        "rag": {
            "mode": "Corpus local découpé par article",
            "embedding_model": settings.OLLAMA_EMBEDDING_MODEL,
            "vector_store": "Mémoire Python (similarité cosinus)",
            "documents": POLICY_ARTICLES,
            "retrieval": "Top 3 par similarité sémantique, puis réponse limitée aux passages retrouvés",
            "next_step": "Importer des conditions générales réelles et migrer les vecteurs vers pgvector",
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
    queryset = Claim.objects.prefetch_related("documents").order_by("-created_at")
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


@api_view(["GET"])
def internal_claim(request, claim_id):
    claim = get_object_or_404(Claim.objects.prefetch_related("documents"), id=claim_id)
    return Response(ClaimSerializer(claim, context={"request": request}).data)


@api_view(["POST"])
def run_document_agent(request):
    claim = get_object_or_404(Claim, id=request.data.get("claim_id"))
    return Response(document_agent(claim))


@api_view(["POST"])
def run_vision_agent(request):
    claim = get_object_or_404(Claim, id=request.data.get("claim_id"))
    return Response(vision_agent(claim))


@api_view(["POST"])
def run_policy_agent(request):
    claim = get_object_or_404(Claim, id=request.data.get("claim_id"))
    return Response(policy_agent(claim))


@api_view(["POST"])
def run_fraud_agent(request):
    return Response(fraud_agent(
        request.data.get("document", {}),
        request.data.get("vision", {}),
        request.data.get("policy", {}),
    ))


@api_view(["POST"])
def run_decision_agent(request):
    return Response(decision_agent(
        request.data.get("document", {}),
        request.data.get("vision", {}),
        request.data.get("policy", {}),
        request.data.get("fraud", {}),
    ))


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
    claim.agent_results = request.data.get("agent_results", {})
    claim.agent_results["decision"] = decision
    claim.error_message = ""
    claim.save()
    return Response(ClaimSerializer(claim, context={"request": request}).data)

