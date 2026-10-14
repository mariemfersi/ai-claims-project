from datetime import date
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from .agents import document_agent, policy_agent, fraud_agent, decision_agent
from .models import Claim


@override_settings(OLLAMA_ENABLED=False)
class AgentPipelineTests(TestCase):
    def setUp(self):
        self.claim = Claim.objects.create(
            customer_name="Client Test",
            policy_number="POL-001",
            description="J'ai eu un accident avec un choc arrière.",
            incident_date=date(2026, 10, 7),
            location="Tunis",
        )

    def test_pipeline_accepts_coherent_covered_claim(self):
        document = document_agent(self.claim)
        document["missing_documents"] = []
        vision = {"damaged_areas": ["rear"]}
        policy = policy_agent(self.claim)
        fraud = fraud_agent(document, vision, policy)
        decision = decision_agent(document, vision, policy, fraud)
        self.assertEqual(decision["decision"], "ACCEPT")
        self.assertEqual(policy["references"][0]["article"], "Article 12")

    @override_settings(N8N_WEBHOOK_URL="")
    def test_api_creates_claim(self):
        response = APIClient().post("/api/claims/", {
            "customer_name": "Client API",
            "policy_number": "POL-002",
            "description": "Accident automobile",
            "incident_date": "2026-10-07",
            "location": "Tunis",
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "SUBMITTED")

