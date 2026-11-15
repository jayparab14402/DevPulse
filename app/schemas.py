from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from .enums import IncidentSeverity, IncidentStatus


class Auth(BaseModel):
    service: str
    level: Literal["INFO", "WARNING", "ERROR", "CRITICAL"]
    message: str
    status_code: int | None = None


class EventResponse(BaseModel):
    id: int
    service: str
    level: Literal["INFO", "WARNING", "ERROR", "CRITICAL"]
    message: str
    status_code: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MonitorCreate(BaseModel):
    name: str
    url: str
    method: str = "GET"
    expected_status: int = 200
    timeout_seconds: float = 5


class MonitorResponse(BaseModel):
    id: int
    name: str
    url: str
    method: str
    expected_status: int
    timeout_seconds: float
    enabled: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MonitorCheckResponse(BaseModel):
    id: int
    monitor_id: int
    status: str
    http_status: int | None
    latency_ms: float | None
    error_message: str | None
    checked_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentResponse(BaseModel):
    id: int
    monitor_id: int
    status: IncidentStatus
    severity: IncidentSeverity
    failure_count: int
    first_seen: datetime
    last_seen: datetime
    created_at: datetime
    resolved_at: datetime | None
    jira_issue_key: str | None
    jira_issue_url: str | None
    jira_sync_status: str
    jira_last_error: str | None
    jira_synced_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
