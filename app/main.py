from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .redis_client import clear_failures
from .schemas import (
    Auth,
    EventResponse,
    IncidentResponse,
    MonitorCheckResponse,
    MonitorCreate,
    MonitorResponse,
)
from .services.incident_service import incident_query, resolve_incident
from .services.monitor_api_service import call_monitor_api_service
from .services.monitor_service import create_monitior_service
from .services.scheduler_service import start_scheduler, stop_scheduler
from .utils import add_record, fetch_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="DevPulse", lifespan=lifespan)


@app.get("/health")
def health_check():
    return {"message": "Hello World"}


@app.post("/events", response_model=EventResponse, status_code=201)
def create_event(req: Auth, db: Session = Depends(get_db)):
    return add_record(db, req)


@app.get("/events", response_model=list[EventResponse])
def get_events(db: Session = Depends(get_db)):
    return fetch_data(db)


@app.post("/monitor", response_model=MonitorResponse, status_code=201)
def create_monitor(req: MonitorCreate, db: Session = Depends(get_db)):
    return create_monitior_service(req, db)


@app.post(
    "/monitor/{monitor_id}/check",
    response_model=MonitorCheckResponse,
)
def check_monitor(monitor_id: int, db: Session = Depends(get_db)):
    return call_monitor_api_service(db, monitor_id)


@app.get("/incidents", response_model=list[IncidentResponse])
def get_incidents(db: Session = Depends(get_db)):
    return incident_query(db)


@app.patch(
    "/incidents/{incident_id}/resolve",
    response_model=IncidentResponse,
)
def resolve_incident_api(
    incident_id: int,
    db: Session = Depends(get_db),
):
    incident = resolve_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Open incident not found")
    clear_failures(incident.monitor_id)
    return incident
