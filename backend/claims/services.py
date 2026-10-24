import mimetypes
import requests
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone


def trigger_n8n(claim):
    if not settings.N8N_WEBHOOK_URL:
        return False
    payload = {
        "claim_id": str(claim.id),
        "claim_url": f"http://backend:8000/api/internal/claims/{claim.id}/",
        "callback_url": f"http://backend:8000/api/internal/claims/{claim.id}/complete/",
        "callback_token": settings.N8N_CALLBACK_TOKEN,
    }
    response = requests.post(settings.N8N_WEBHOOK_URL, json=payload, timeout=10)
    response.raise_for_status()
    claim.status = claim.Status.PROCESSING
    claim.agent_results = {
        "history": claim.agent_results.get("history", []) if isinstance(claim.agent_results, dict) else [],
        "timeline": {
            "started_at": timezone.now().isoformat(),
            "agents": {
                "document": {"status": "PENDING", "expected_seconds": 180},
                "vision": {"status": "PENDING", "expected_seconds": 150},
                "policy": {"status": "PENDING", "expected_seconds": 90},
                "fraud": {"status": "PENDING", "expected_seconds": 3},
                "decision": {"status": "PENDING", "expected_seconds": 3},
            },
        },
    }
    claim.save(update_fields=["status", "agent_results", "updated_at"])
    return True


def send_claim_handoff_email(claim):
    contact = claim.assigned_contact
    if not contact or not contact.email:
        return "NOT_CONFIGURED", "Le responsable n’a pas d’adresse email.", None
    if not settings.EMAIL_HOST or not settings.DEFAULT_FROM_EMAIL:
        return "NOT_CONFIGURED", "Configure le serveur SMTP dans le fichier .env.", None

    reasons = "\n".join(f"- {reason}" for reason in claim.reasons) or "- Aucune justification détaillée fournie."
    lines = [
        f"Bonjour {contact.name},",
        "",
        "Un dossier de sinistre nécessitant une vérification vous a été transmis.",
        "",
        f"Client : {claim.customer_name}",
        f"Contrat : {claim.policy_number}",
        f"Dossier : {claim.id}",
        f"Date du sinistre : {claim.incident_date}",
        f"Lieu : {claim.location}",
        f"Décision automatique : {claim.get_decision_display()}",
        f"Score de risque : {claim.risk_score if claim.risk_score is not None else '—'}/100",
        f"Confiance : {round((claim.confidence or 0) * 100)}%",
        "",
        "Déclaration :",
        claim.description,
        "",
        "Motifs de vérification :",
        reasons,
        "",
        f"Note de transmission : {claim.handoff_note or 'Aucune note.'}",
        "",
        "Les pièces jointes suivent après préparation du message.",
    ]
    email = EmailMessage(
        subject=f"Dossier à examiner — {claim.customer_name} — {claim.policy_number}",
        body="\n".join(lines),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[contact.email],
    )

    total_size = 0
    attached_names = []
    skipped_names = []
    for document in claim.documents.all():
        try:
            size = document.file.size
            if total_size + size > settings.EMAIL_MAX_ATTACHMENT_BYTES:
                skipped_names.append(document.original_name)
                continue
            with document.file.open("rb") as stream:
                content = stream.read(settings.EMAIL_MAX_ATTACHMENT_BYTES - total_size + 1)
            if total_size + len(content) > settings.EMAIL_MAX_ATTACHMENT_BYTES:
                skipped_names.append(document.original_name)
                continue
            content_type = document.mime_type or mimetypes.guess_type(document.original_name)[0] or "application/octet-stream"
            email.attach(document.original_name, content, content_type)
            total_size += len(content)
            attached_names.append(document.original_name)
        except (OSError, ValueError):
            skipped_names.append(document.original_name)
            continue

    email.body += f"\n\nPièces jointes : {len(attached_names)} sur {claim.documents.count()}."
    if skipped_names:
        email.body += "\nFichiers non joints (taille limite dépassée ou fichier inaccessible) :\n"
        email.body += "\n".join(f"- {name}" for name in skipped_names)

    try:
        sent_count = email.send(fail_silently=False)
    except Exception as exc:
        return "FAILED", f"{type(exc).__name__}: vérifie les identifiants et paramètres SMTP.", None
    if not sent_count:
        return "FAILED", "Le serveur SMTP n’a confirmé aucun envoi.", None
    return "SENT", "", timezone.now()

