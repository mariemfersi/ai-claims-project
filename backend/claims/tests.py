from datetime import date
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from .agents import _compare_pdf_texts, _normalize_policy_payload, _normalize_vision_analysis, document_agent, policy_agent, vision_agent, fraud_agent, decision_agent
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

    def test_pdf_comparison_reports_shared_text_and_prefers_native_layer(self):
        text = "Le véhicule assuré est couvert contre les dommages accidentels."
        comparison = _compare_pdf_texts(text, text, 1)
        self.assertEqual(comparison["status"], "compared")
        self.assertEqual(comparison["selected_method"], "pypdf")
        self.assertEqual(comparison["similarity"], 1.0)
        self.assertIn("véhicule assuré", comparison["shared_text"])

    def test_pdf_comparison_uses_ocr_for_scanned_document(self):
        ocr_text = "Une déclaration de sinistre avec un conducteur assuré et un véhicule identifié."
        comparison = _compare_pdf_texts("", ocr_text, 2)
        self.assertEqual(comparison["selected_method"], "ocr")
        self.assertEqual(comparison["pypdf_characters"], 0)
        self.assertEqual(comparison["ocr_characters"], len(ocr_text))

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

    @override_settings(OLLAMA_ENABLED=True)
    @patch("claims.agents._local_retrieve", return_value=[])
    @patch("claims.agents._retrieve", return_value=[])
    @patch("claims.agents._parse", return_value={
        "coverage_status": "covered",
        "applicable_articles": ["Page 42"],
        "explanation": "Le modèle affirme que la garantie est couverte.",
        "missing_information": [],
        "confidence": 1.0,
    })
    def test_policy_never_confirms_coverage_without_particular_conditions(self, *_mocks):
        policy = policy_agent(self.claim)
        self.assertEqual(policy["coverage_status"], "insufficient_information")
        self.assertIn("Conditions particulières et garanties souscrites", policy["missing_information"])

    @override_settings(OLLAMA_ENABLED=True)
    @patch("claims.agents._local_retrieve", return_value=[])
    @patch("claims.agents._retrieve", return_value=[])
    @patch("claims.agents._parse", return_value={
        "coverage_status": "insufficient_information",
        "applicable_articles": ["Garantie dommages collision"],
        "explanation": "La garantie est active, mais le modèle reste incertain.",
        "missing_information": ["Garanties souscrites"],
        "confidence": 0.5,
    })
    def test_policy_resolves_llm_uncertainty_from_explicit_demo_collision_coverage(self, *_mocks):
        self.claim.location = "Lyon, France"
        self.claim.policy_number = "AXA-FR-DEMO-2026-0042"
        self.claim.save(update_fields=["location", "policy_number"])
        ClaimDocument.objects.create(
            claim=self.claim,
            file=SimpleUploadedFile(
                "03_conditions_particulieres_demo.txt",
                b"Contrat AXA-FR-DEMO-2026-0042. Garantie dommages collision souscrite et active.",
                content_type="text/plain",
            ),
            original_name="03_conditions_particulieres_demo.txt",
            mime_type="text/plain",
            kind="OTHER",
        )
        policy = policy_agent(self.claim)
        self.assertEqual(policy["coverage_status"], "covered")
        self.assertGreaterEqual(policy["confidence"], 0.9)
        self.assertEqual(policy["missing_information"], [])

    @override_settings(OLLAMA_ENABLED=True)
    @patch("claims.agents._image_content", return_value=[])
    @patch("claims.agents._parse", return_value={
        "visible_damage": True,
        "damaged_areas": ["front"],
        "damage_types": ["bumper"],
        "severity": "medium",
        "image_quality": "good",
        "observations": ["Choc visible à l'avant."],
        "confidence": 0.8,
    })
    def test_vision_flags_conflict_with_explicit_photo_view_label(self, *_mocks):
        ClaimDocument.objects.create(
            claim=self.claim,
            file=SimpleUploadedFile("photo.png", b"not-an-image", content_type="image/png"),
            original_name="04_photo_vue_arriere.png",
            mime_type="image/png",
            kind="PHOTO",
        )
        result = vision_agent(self.claim)
        self.assertEqual(result["engine"], "ollama")
        self.assertEqual(result["analysis_status"], "incomplete")
        self.assertEqual(result["diagnostic_error"], "PhotoViewConflict")

    def test_vision_area_is_recovered_from_observations(self):
        normalized = _normalize_vision_analysis({
            "visible_damage": True,
            "damaged_areas": [],
            "observations": ["Damage to the rear end, trunk and taillight."],
        })
        self.assertEqual(normalized["damaged_areas"], ["rear"])

    def test_vision_normalizer_uses_zones_and_discards_freeform_claims(self):
        normalized = _normalize_vision_analysis({
            "damaged_areas": ["rear"],
            "observations": ["Possible damage on the roof and garage door."],
        })
        self.assertTrue(normalized["visible_damage"])
        self.assertEqual(normalized["observations"], [])

    def test_vision_fallback_does_not_guess_damage_area_from_claim_text(self):
        self.claim.description = "Choc à l'avant du véhicule."
        self.claim.save(update_fields=["description"])
        ClaimDocument.objects.create(
            claim=self.claim,
            file=SimpleUploadedFile("photo.png", b"not-an-image", content_type="image/png"),
            original_name="photo.png",
            mime_type="image/png",
            kind="PHOTO",
        )
        result = vision_agent(self.claim)
        self.assertFalse(result["visible_damage"])
        self.assertEqual(result["damaged_areas"], [])
        self.assertEqual(result["analysis_status"], "incomplete")

    def test_fraud_detects_bidirectional_damage_mismatch(self):
        policy = {"coverage_status": "covered"}
        rear_declaration = {"claim_facts": {"description": "Choc à l'arrière"}, "missing_documents": []}
        front_declaration = {"claim_facts": {"description": "Choc frontal à l'avant"}, "missing_documents": []}
        self.assertEqual(fraud_agent(rear_declaration, {"damaged_areas": ["front"]}, policy)["risk_score"], 50)
        self.assertEqual(fraud_agent(front_declaration, {"damaged_areas": ["rear"]}, policy)["risk_score"], 50)

    def test_fraud_does_not_count_mismatch_from_incomplete_vision(self):
        document = {"claim_facts": {"description": "Choc à l'arrière"}, "missing_documents": []}
        vision = {"analysis_status": "incomplete", "diagnostic_error": "PhotoViewConflict", "damaged_areas": ["front"]}
        result = fraud_agent(document, vision, {"coverage_status": "covered"})
        self.assertIsNone(result["risk_score"])
        self.assertEqual(result["observed_risk_score"], 0)
        self.assertNotIn("damage_location_mismatch", [item["type"] for item in result["inconsistencies"]])

    def test_vision_fallback_does_not_report_a_zero_fraud_score_as_complete(self):
        document = {"claim_facts": {"description": "Choc à l'avant"}, "missing_documents": []}
        vision = {"engine": "local-fallback", "analysis_status": "incomplete", "visible_damage": True, "photos": ["photo.png"], "damaged_areas": ["front"]}
        policy = {"coverage_status": "covered", "references": []}
        fraud = fraud_agent(document, vision, policy)
        decision = decision_agent(document, vision, policy, fraud)
        self.assertEqual(fraud["assessment_status"], "incomplete")
        self.assertIsNone(fraud["risk_score"])
        self.assertEqual(decision["decision"], "INVESTIGATE")
        self.assertIsNone(decision["risk_score"])

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

