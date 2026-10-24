from datetime import date
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from .agents import _normalize_policy_payload, _normalize_vision_analysis, document_agent, policy_agent, fraud_agent, decision_agent
from .models import Claim, ClaimDocument


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

    def test_pipeline_requires_particular_conditions_without_llm(self):
        document = document_agent(self.claim)
        document["missing_documents"] = []
        vision = {"damaged_areas": ["rear"]}
        policy = policy_agent(self.claim)
        fraud = fraud_agent(document, vision, policy)
        decision = decision_agent(document, vision, policy, fraud)
        self.assertEqual(decision["decision"], "INVESTIGATE")
        self.assertEqual(policy["coverage_status"], "insufficient_information")
        self.assertEqual(policy["references"][0]["insurer"], "AXA France")

    def test_decision_rejects_only_an_explicit_exclusion(self):
        document = {"missing_documents": []}
        vision = {"visible_damage": True}
        fraud = {"risk_score": 0, "inconsistencies": []}
        excluded = {"coverage_status": "excluded", "explanation": "Exclusion explicite.", "references": []}
        covered = {"coverage_status": "covered", "explanation": "Garantie confirmée.", "references": []}
        self.assertEqual(decision_agent(document, vision, excluded, fraud)["decision"], "REJECT")
        self.assertEqual(decision_agent(document, vision, covered, fraud)["decision"], "ACCEPT")

    def test_policy_payload_normalizes_local_llm_variations(self):
        normalized = _normalize_policy_payload({
            "coverage_status": "inconnu",
            "applicable_articles": [{"page": 34}],
            "explanation": ["Conditions particulières", "requises"],
            "missing_information": "Garanties souscrites",
            "confidence": 75,
        })
        self.assertEqual(normalized["coverage_status"], "insufficient_information")
        self.assertEqual(normalized["applicable_articles"], ["Page 34"])
        self.assertEqual(normalized["confidence"], 0.75)

    def test_vision_area_is_recovered_from_observations(self):
        normalized = _normalize_vision_analysis({
            "visible_damage": True,
            "damaged_areas": [],
            "observations": ["Damage to the rear end, trunk and taillight."],
        })
        self.assertEqual(normalized["damaged_areas"], ["rear"])

    def test_fraud_detects_bidirectional_damage_mismatch(self):
        policy = {"coverage_status": "covered"}
        rear_declaration = {"claim_facts": {"description": "Choc à l'arrière"}, "missing_documents": []}
        front_declaration = {"claim_facts": {"description": "Choc frontal à l'avant"}, "missing_documents": []}
        self.assertEqual(fraud_agent(rear_declaration, {"damaged_areas": ["front"]}, policy)["risk_score"], 50)
        self.assertEqual(fraud_agent(front_declaration, {"damaged_areas": ["rear"]}, policy)["risk_score"], 50)

    def test_decision_includes_fraud_evidence_when_coverage_is_unknown(self):
        document = {"missing_documents": []}
        vision = {"visible_damage": True}
        policy = {"coverage_status": "insufficient_information", "explanation": "Contrat à vérifier.", "references": []}
        fraud = {"risk_score": 50, "inconsistencies": [{"evidence": "Zones contradictoires."}]}
        result = decision_agent(document, vision, policy, fraud)
        self.assertEqual(result["decision"], "INVESTIGATE")
        self.assertIn("Zones contradictoires.", result["reasons"])

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

    @override_settings(N8N_WEBHOOK_URL="")
    def test_completed_claim_accepts_new_files_and_resets_decision(self):
        self.claim.status = Claim.Status.COMPLETED
        self.claim.decision = Claim.Decision.REJECT
        self.claim.confidence = 0.7
        self.claim.risk_score = 20
        self.claim.save()
        uploaded = SimpleUploadedFile("facture_complementaire.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        response = APIClient().post(f"/api/claims/{self.claim.id}/add-files/", {"files": [uploaded]}, format="multipart")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "SUBMITTED")
        self.assertEqual(response.data["decision"], "")
        self.assertEqual(len(response.data["documents"]), 1)
        self.assertEqual(response.data["agent_results"]["history"][0]["decision"], "REJECT")

    @override_settings(N8N_WEBHOOK_URL="")
    def test_completed_claim_can_delete_keep_and_replace_files(self):
        self.claim.status = Claim.Status.COMPLETED
        self.claim.decision = Claim.Decision.ACCEPT
        self.claim.save()
        kept = ClaimDocument.objects.create(
            claim=self.claim,
            file=SimpleUploadedFile("constat.pdf", b"constat", content_type="application/pdf"),
            original_name="constat.pdf",
            mime_type="application/pdf",
        )
        ClaimDocument.objects.create(
            claim=self.claim,
            file=SimpleUploadedFile("ancienne-photo.jpg", b"photo", content_type="image/jpeg"),
            original_name="ancienne-photo.jpg",
            mime_type="image/jpeg",
        )
        replacement = SimpleUploadedFile("nouvelle-photo.jpg", b"new-photo", content_type="image/jpeg")
        response = APIClient().post(
            f"/api/claims/{self.claim.id}/add-files/",
            {"keep_document_ids": [str(kept.id)], "files": [replacement]},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {document["original_name"] for document in response.data["documents"]},
            {"constat.pdf", "nouvelle-photo.jpg"},
        )

