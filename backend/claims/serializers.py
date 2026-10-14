from rest_framework import serializers
from .models import Claim, ClaimDocument


class ClaimDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClaimDocument
        fields = ["id", "kind", "file", "original_name", "mime_type", "created_at"]
        read_only_fields = ["id", "original_name", "mime_type", "created_at"]


class ClaimSerializer(serializers.ModelSerializer):
    documents = ClaimDocumentSerializer(many=True, read_only=True)
    files = serializers.ListField(
        child=serializers.FileField(), write_only=True, required=False
    )

    class Meta:
        model = Claim
        fields = [
            "id", "customer_name", "policy_number", "description", "incident_date",
            "location", "status", "decision", "confidence", "risk_score", "reasons",
            "policy_references", "agent_results", "error_message", "documents", "files",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "status", "decision", "confidence", "risk_score", "reasons",
            "policy_references", "agent_results", "error_message", "created_at", "updated_at",
        ]

    def create(self, validated_data):
        files = validated_data.pop("files", [])
        claim = Claim.objects.create(**validated_data)
        for uploaded in files:
            ClaimDocument.objects.create(
                claim=claim,
                kind=self._kind_from_content_type(uploaded.content_type, uploaded.name),
                file=uploaded,
                original_name=uploaded.name,
                mime_type=uploaded.content_type or "",
            )
        return claim

    @staticmethod
    def _kind_from_content_type(content_type, name):
        lower = name.lower()
        if (content_type or "").startswith("image/"):
            return ClaimDocument.Kind.PHOTO
        if (content_type or "").startswith("audio/"):
            return ClaimDocument.Kind.AUDIO
        if "facture" in lower or "invoice" in lower:
            return ClaimDocument.Kind.INVOICE
        if "constat" in lower or "report" in lower:
            return ClaimDocument.Kind.REPORT
        if "form" in lower:
            return ClaimDocument.Kind.FORM
        return ClaimDocument.Kind.OTHER

