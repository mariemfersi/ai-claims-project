import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Claim",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("customer_name", models.CharField(max_length=160)),
                ("policy_number", models.CharField(max_length=80)),
                ("description", models.TextField()),
                ("incident_date", models.DateField()),
                ("location", models.CharField(max_length=200)),
                ("status", models.CharField(choices=[("SUBMITTED", "Soumis"), ("PROCESSING", "En traitement"), ("COMPLETED", "Terminé"), ("FAILED", "Échec")], default="SUBMITTED", max_length=20)),
                ("decision", models.CharField(blank=True, choices=[("ACCEPT", "Accepté"), ("INVESTIGATE", "À examiner"), ("REJECT", "Refusé")], max_length=20)),
                ("confidence", models.FloatField(blank=True, null=True)),
                ("risk_score", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("reasons", models.JSONField(blank=True, default=list)),
                ("policy_references", models.JSONField(blank=True, default=list)),
                ("agent_results", models.JSONField(blank=True, default=dict)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="ClaimDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("FORM", "Formulaire"), ("REPORT", "Constat"), ("INVOICE", "Facture"), ("PHOTO", "Photo"), ("AUDIO", "Audio"), ("OTHER", "Autre")], default="OTHER", max_length=20)),
                ("file", models.FileField(upload_to="claims/%Y/%m/%d/")),
                ("original_name", models.CharField(max_length=255)),
                ("mime_type", models.CharField(blank=True, max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("claim", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="documents", to="claims.claim")),
            ],
        ),
    ]

