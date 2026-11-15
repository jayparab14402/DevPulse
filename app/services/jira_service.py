import os
from datetime import datetime, timezone

import requests
from requests.auth import HTTPBasicAuth


JIRA_TIMEOUT_SECONDS = 5


def _is_enabled() -> bool:
    return os.getenv("JIRA_INTEGRATION_ENABLED", "false").lower() == "true"


def create_jira_issue(incident):
    """Create one Jira issue for a newly-created DevPulse incident."""
    if not _is_enabled():
        return {
            "status": "DISABLED",
            "error": None,
        }

    base_url = os.getenv("JIRA_BASE_URL")
    email = os.getenv("JIRA_EMAIL")
    api_token = os.getenv("JIRA_API_TOKEN")
    project_key = os.getenv("JIRA_PROJECT_KEY", "KAN")
    issue_type = os.getenv("JIRA_ISSUE_TYPE", "Task")

    if not base_url or not email or not api_token:
        return {
            "status": "NOT_CONFIGURED",
            "error": "Jira environment variables are incomplete",
        }

    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": (
                f"[DevPulse] Monitor {incident.monitor_id} incident "
                f"{incident.id} is OPEN"
            ),
            "issuetype": {"name": issue_type},
            "labels": [
                "devpulse",
                f"devpulse-incident-{incident.id}",
            ],
        }
    }

    try:
        response = requests.post(
            f"{base_url.rstrip('/')}/rest/api/3/issue",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            auth=HTTPBasicAuth(email, api_token),
            json=payload,
            timeout=JIRA_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        issue_key = response.json().get("key")
        if not issue_key:
            return {
                "status": "FAILED",
                "error": "Jira response did not include an issue key",
            }

        return {
            "status": "CREATED",
            "issue_key": issue_key,
            "issue_url": f"{base_url.rstrip('/')}/browse/{issue_key}",
            "synced_at": datetime.now(timezone.utc),
            "error": None,
        }
    except requests.RequestException as exc:
        status_code = exc.response.status_code if exc.response is not None else None
        error = (
            f"Jira request failed with HTTP {status_code}"
            if status_code
            else "Jira request failed because of a connection error"
        )
        return {
            "status": "FAILED",
            "error": error,
        }
