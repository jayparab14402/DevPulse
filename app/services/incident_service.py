
from sqlalchemy import Select
from ..models import Monitor, MonitorCheck, Incident, IncidentStatus, IncidentSeverity
from datetime import datetime, timezone



def incident_query(conn):
    query = Select(Incident)
    return conn.scalars(query).all()

def handle_incident(conn, monitor_id, failure_count):

    if failure_count < 3:
        return None

    query = Select(Incident).where(
        Incident.monitor_id == monitor_id,
        Incident.status == IncidentStatus.OPEN
    )

    incident = conn.scalars(query).first()

    if incident is None:
        incident = Incident(
            monitor_id=monitor_id,
            status=IncidentStatus.OPEN,
            severity=IncidentSeverity.HIGH,
            failure_count=failure_count
        )

        conn.add(incident)

    else:
        incident.failure_count = failure_count
        incident.last_seen = datetime.now(timezone.utc)

    conn.commit()
    conn.refresh(incident)

    return incident