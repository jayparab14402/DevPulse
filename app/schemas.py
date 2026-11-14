'''

{
  "service": "auth-service",
  "level": "ERROR",
  "message": "Database connection timeout",
  "status_code": 500
}

1. app/ ke andar ek alag file banao for Pydantic schema, something like schemas.py.
2. Ek model banao jo above fields validate kare.
3. level ko initially simple string rehne do.
4. status_code optional hona chahiye, because har incident HTTP-based nahi hoga.
5. main.py mein POST /events endpoint banao.
6. Abhi database nahi hai, so jo request aayi wahi validated response mein return kar do.
7. Swagger /docs se test karo.
'''

from pydantic import BaseModel
from typing import Literal
from datetime import datetime
from pydantic import ConfigDict
from .enums import IncidentStatus, IncidentSeverity

class Auth(BaseModel):
    service: str
    level: Literal["INFO", "WARNING", "ERROR", "CRITICAL"]
    message: str
    status_code: int | None

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

    model_config = ConfigDict(from_attributes=True)