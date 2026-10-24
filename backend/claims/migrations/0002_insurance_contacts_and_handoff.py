import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("claims", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="InsuranceContact",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("role", models.CharField(max_length=120)),
                ("insurer", models.CharField(blank=True, max_length=160)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("phone", models.CharField(blank=True, max_length=40)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["insurer", "name"]},
        ),
        migrations.AddField(
            model_name="claim",
            name="assigned_contact",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_claims", to="claims.insurancecontact"),
        ),
        migrations.AddField(
            model_name="claim",
            name="handoff_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="claim",
            name="handoff_note",
            field=models.TextField(blank=True),
        ),
    ]
