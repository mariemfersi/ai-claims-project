from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("claims", "0002_insurance_contacts_and_handoff")]

    operations = [
        migrations.AddField(
            model_name="claim",
            name="handoff_email_status",
            field=models.CharField(blank=True, max_length=24),
        ),
        migrations.AddField(
            model_name="claim",
            name="handoff_email_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="claim",
            name="handoff_email_error",
            field=models.TextField(blank=True),
        ),
    ]
