import os

import requests

from ..models import Incident


def send_incident_alert(incident: Incident) -> bool:
    """Send one Slack alert for a newly-created incident, when configured."""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return False

    message = (
        "🚨 DevPulse Incident\n\n"
        f"Monitor ID: {incident.monitor_id}\n"
        f"Severity: {incident.severity.value}\n"
        f"Failures: {incident.failure_count}\n"
        f"Status: {incident.status.value}"
    )

    try:
        response = requests.post(webhook_url, json={"text": message}, timeout=5)
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        print(f"Slack alert failed: {exc}")
        return False
