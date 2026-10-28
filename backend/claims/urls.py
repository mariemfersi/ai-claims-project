from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (
    ClaimViewSet, internal_claim, complete_claim, run_document_agent,
    run_vision_agent, run_policy_agent, run_fraud_agent, run_decision_agent, system_info,
    InsuranceContactViewSet, run_specialist_agents,
)

router = DefaultRouter()
router.register("claims", ClaimViewSet, basename="claim")
router.register("contacts", InsuranceContactViewSet, basename="insurance-contact")

urlpatterns = [
    path("", include(router.urls)),
    path("internal/claims/<uuid:claim_id>/", internal_claim),
    path("internal/claims/<uuid:claim_id>/complete/", complete_claim),
    path("internal/agents/document/", run_document_agent),
    path("internal/agents/specialists/", run_specialist_agents),
    path("internal/agents/vision/", run_vision_agent),
    path("internal/agents/policy/", run_policy_agent),
    path("internal/agents/fraud/", run_fraud_agent),
    path("internal/agents/decision/", run_decision_agent),
    path("system/info/", system_info),
]

