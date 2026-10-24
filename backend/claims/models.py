import uuid
from django.db import models


class Claim(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Soumis"
        PROCESSING = "PROCESSING", "En traitement"
        COMPLETED = "COMPLETED", "Terminé"
        FAILED = "FAILED", "Échec"

    class Decision(models.TextChoices):
        ACCEPT = "ACCEPT", "Accepté"
        INVESTIGATE = "INVESTIGATE", "À examiner"
        REJECT = "REJECT", "Refusé"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_name = models.CharField(max_length=160)
    policy_number = models.CharField(max_length=80)
    description = models.TextField()
    incident_date = models.DateField()
    location = models.CharField(max_length=200)
    assigned_contact = models.ForeignKey("InsuranceContact", related_name="assigned_claims", null=True, blank=True, on_delete=models.SET_NULL)
    handoff_at = models.DateTimeField(null=True, blank=True)
    handoff_note = models.TextField(blank=True)
    handoff_email_status = models.CharField(max_length=24, blank=True)
    handoff_email_sent_at = models.DateTimeField(null=True, blank=True)
    handoff_email_error = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    decision = models.CharField(max_length=20, choices=Decision.choices, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    risk_score = models.PositiveSmallIntegerField(null=True, blank=True)
    reasons = models.JSONField(default=list, blank=True)
    policy_references = models.JSONField(default=list, blank=True)
    agent_results = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} - {self.customer_name}"


class InsuranceContact(models.Model):
    name = models.CharField(max_length=160)
    role = models.CharField(max_length=120)
    insurer = models.CharField(max_length=160, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["insurer", "name"]

    def __str__(self):
        return f"{self.name} — {self.role}"


class ClaimDocument(models.Model):
    class Kind(models.TextChoices):
        FORM = "FORM", "Formulaire"
        REPORT = "REPORT", "Constat"
        INVOICE = "INVOICE", "Facture"
        PHOTO = "PHOTO", "Photo"
        AUDIO = "AUDIO", "Audio"
        OTHER = "OTHER", "Autre"

    claim = models.ForeignKey(Claim, related_name="documents", on_delete=models.CASCADE)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.OTHER)
    file = models.FileField(upload_to="claims/%Y/%m/%d/")
    original_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

