from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# 1. Health check
def test_health():
    resp = client.get("/health")

    assert resp.status_code == 200
    assert resp.json() == {"message": "Hello World"}


# 2. Valid event create
def test_create_event():
    payload = {
        "service": "pytest-service",
        "level": "INFO",
        "message": "Testing event creation",
        "status_code": 200
    }

    resp = client.post("/events", json=payload)

    assert resp.status_code == 201

    data = resp.json()

    assert data["service"] == "pytest-service"
    assert data["level"] == "INFO"
    assert data["message"] == "Testing event creation"
    assert data["status_code"] == 200
    assert "id" in data
    assert "created_at" in data


# 3. Invalid enum/level
def test_invalid_level():
    payload = {
        "service": "pytest-service",
        "level": "PAGAL",
        "message": "Invalid level test",
        "status_code": 500
    }

    resp = client.post("/events", json=payload)

    assert resp.status_code == 422


# 4. Missing required field
def test_missing_service():
    payload = {
        "level": "ERROR",
        "message": "Service field missing",
        "status_code": 500
    }

    resp = client.post("/events", json=payload)

    assert resp.status_code == 422


# 5. Fetch events
def test_get_events():
    resp = client.get("/events")

    assert resp.status_code == 200
    assert isinstance(resp.json(), list)