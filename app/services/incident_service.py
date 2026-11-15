from datetime import datetime, timezone

from sqlalchemy import select

from ..enums import IncidentSeverity, IncidentStatus
from ..models import Incident


INCIDENT_FAILURE_THRESHOLD = 3


def incident_query(session):
    return session.scalars(select(Incident)).all()


def handle_incident(session, monitor_id: int, failure_count: int):
    """Create or update an incident and report whether it was newly created."""
    if failure_count < INCIDENT_FAILURE_THRESHOLD:
        return None, False

    incident = session.scalars(
        select(Incident).where(
            Incident.monitor_id == monitor_id,
            Incident.status == IncidentStatus.OPEN,
        )
    ).first()

    created = incident is None
    if created:
        incident = Incident(
            monitor_id=monitor_id,
            status=IncidentStatus.OPEN,
            severity=IncidentSeverity.HIGH,
            failure_count=failure_count,
        )
        session.add(incident)
    else:
        incident.failure_count = failure_count
        incident.last_seen = datetime.now(timezone.utc)

    session.commit()
    session.refresh(incident)
    return incident, created


def resolve_incident(session, incident_id: int):
    incident = session.scalars(
        select(Incident).where(
            Incident.id == incident_id,
            Incident.status == IncidentStatus.OPEN,
        )
    ).first()

    if incident is None:
        return None

    incident.status = IncidentStatus.RESOLVED
    incident.resolved_at = datetime.now(timezone.utc)

    session.commit()
    session.refresh(incident)
    return incident
