import os
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
import requests
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.main import app
from app.models import Base, Monitor
from app.redis_client import register_failure
from app.services import scheduler_service
from app.services.jira_service import create_jira_issue


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def override_get_db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
    yield


def create_monitor(name="Example API", expected_status=200):
    response = client.post(
        "/monitor",
        json={
            "name": name,
            "url": "https://example.com/health",
            "method": "GET",
            "expected_status": expected_status,
            "timeout_seconds": 5,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_event_create_validation_and_list():
    payload = {
        "service": "pytest-service",
        "level": "INFO",
        "message": "Testing event creation",
    }
    response = client.post("/events", json=payload)
    assert response.status_code == 201
    assert response.json()["status_code"] is None

    invalid = client.post("/events", json={**payload, "level": "INVALID"})
    assert invalid.status_code == 422

    events = client.get("/events")
    assert events.status_code == 200
    assert len(events.json()) == 1


def test_monitor_check_up():
    monitor = create_monitor()
    external_response = Mock(status_code=200)

    with patch(
        "app.services.monitor_api_service.requests.request",
        return_value=external_response,
    ):
        response = client.post(f"/monitor/{monitor['id']}/check")

    assert response.status_code == 200
    assert response.json()["status"] == "UP"
    assert response.json()["http_status"] == 200


def test_request_error_creates_down_check():
    monitor = create_monitor()

    with (
        patch(
            "app.services.monitor_api_service.requests.request",
            side_effect=requests.Timeout("request timed out"),
        ),
        patch(
            "app.services.monitor_api_service.register_failure",
            return_value=1,
        ),
    ):
        response = client.post(f"/monitor/{monitor['id']}/check")

    assert response.status_code == 200
    assert response.json()["status"] == "DOWN"
    assert response.json()["http_status"] is None
    assert "timed out" in response.json()["error_message"]


def test_failure_lifecycle_and_resolve():
    monitor = create_monitor(expected_status=200)
    external_response = Mock(status_code=503)

    with (
        patch(
            "app.services.monitor_api_service.requests.request",
            return_value=external_response,
        ),
        patch(
            "app.services.monitor_api_service.register_failure",
            side_effect=[1, 2, 3, 4],
        ),
        patch(
            "app.services.monitor_api_service.send_incident_alert"
        ) as send_alert,
        patch(
            "app.services.monitor_api_service.create_jira_issue",
            return_value={
                "status": "CREATED",
                "issue_key": "KAN-1",
                "issue_url": "https://example.atlassian.net/browse/KAN-1",
                "error": None,
            },
        ) as create_jira,
    ):
        first = client.post(f"/monitor/{monitor['id']}/check")
        assert first.json()["status"] == "DOWN"
        assert client.get("/incidents").json() == []

        second = client.post(f"/monitor/{monitor['id']}/check")
        assert second.json()["status"] == "DOWN"
        assert client.get("/incidents").json() == []

        third = client.post(f"/monitor/{monitor['id']}/check")
        incidents = client.get("/incidents").json()
        assert len(incidents) == 1
        incident_id = incidents[0]["id"]
        assert incidents[0]["failure_count"] == 3
        assert incidents[0]["status"] == "OPEN"
        assert incidents[0]["jira_issue_key"] == "KAN-1"
        assert incidents[0]["jira_sync_status"] == "CREATED"

        fourth = client.post(f"/monitor/{monitor['id']}/check")
        incidents = client.get("/incidents").json()
        assert len(incidents) == 1
        assert incidents[0]["id"] == incident_id
        assert incidents[0]["failure_count"] == 4

        send_alert.assert_called_once()
        create_jira.assert_called_once()

    with patch("app.main.clear_failures") as clear_failures:
        resolved = client.patch(f"/incidents/{incident_id}/resolve")

    assert resolved.status_code == 200
    assert resolved.json()["status"] == "RESOLVED"
    assert resolved.json()["resolved_at"] is not None
    clear_failures.assert_called_once_with(monitor["id"])

    already_resolved = client.patch(f"/incidents/{incident_id}/resolve")
    assert already_resolved.status_code == 404


def test_missing_monitor_returns_404():
    response = client.post("/monitor/999/check")
    assert response.status_code == 404


def test_redis_ttl_is_set_only_for_first_failure():
    redis_mock = Mock()
    redis_mock.incr.side_effect = [1, 2]

    with patch("app.redis_client.redis_client", redis_mock):
        assert register_failure(7) == 1
        assert register_failure(7) == 2

    redis_mock.expire.assert_called_once_with("monitor:7:failures", 300)


def test_jira_integration_is_disabled_by_default():
    incident = SimpleNamespace(id=10, monitor_id=7)

    with (
        patch.dict(os.environ, {"JIRA_INTEGRATION_ENABLED": "false"}),
        patch("app.services.jira_service.requests.post") as jira_post,
    ):
        result = create_jira_issue(incident)

    assert result["status"] == "DISABLED"
    jira_post.assert_not_called()


def test_jira_issue_creation_uses_one_request():
    incident = SimpleNamespace(id=10, monitor_id=7)
    jira_response = Mock()
    jira_response.json.return_value = {"key": "KAN-25"}

    jira_environment = {
        "JIRA_INTEGRATION_ENABLED": "true",
        "JIRA_BASE_URL": "https://example.atlassian.net",
        "JIRA_EMAIL": "developer@example.com",
        "JIRA_API_TOKEN": "test-token",
        "JIRA_PROJECT_KEY": "KAN",
        "JIRA_ISSUE_TYPE": "Task",
    }

    with (
        patch.dict(os.environ, jira_environment),
        patch(
            "app.services.jira_service.requests.post",
            return_value=jira_response,
        ) as jira_post,
    ):
        result = create_jira_issue(incident)

    assert result["status"] == "CREATED"
    assert result["issue_key"] == "KAN-25"
    assert result["issue_url"] == "https://example.atlassian.net/browse/KAN-25"
    jira_post.assert_called_once()

    request_payload = jira_post.call_args.kwargs["json"]
    assert request_payload["fields"]["project"]["key"] == "KAN"
    assert "devpulse-incident-10" in request_payload["fields"]["labels"]


def test_scheduler_checks_only_enabled_monitors():
    session = TestingSessionLocal()
    session.add_all(
        [
            Monitor(
                name="Enabled",
                url="https://example.com/health",
                method="GET",
                expected_status=200,
                timeout_seconds=5,
                enabled=True,
            ),
            Monitor(
                name="Disabled",
                url="https://example.com/health",
                method="GET",
                expected_status=200,
                timeout_seconds=5,
                enabled=False,
            ),
        ]
    )
    session.commit()
    enabled_id = session.query(Monitor).filter_by(enabled=True).one().id
    session.close()

    with (
        patch.object(
            scheduler_service,
            "SessionLocal",
            TestingSessionLocal,
        ),
        patch.object(
            scheduler_service,
            "call_monitor_api_service",
        ) as call_monitor,
    ):
        scheduler_service.monitor_job()

    call_monitor.assert_called_once()
    assert call_monitor.call_args.args[1] == enabled_id
