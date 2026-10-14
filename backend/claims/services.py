import requests
from django.conf import settings


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
    claim.save(update_fields=["status", "updated_at"])
    return True

