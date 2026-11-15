import time

import requests
from fastapi import HTTPException
from sqlalchemy import select

from ..enums import MonitorStatus
from ..models import Monitor, MonitorCheck
from ..redis_client import register_failure
from .incident_service import handle_incident
from .slack_service import send_incident_alert


def _save_check(session, check: MonitorCheck) -> MonitorCheck:
    session.add(check)
    session.commit()
    session.refresh(check)
    return check


def _process_failure(session, check: MonitorCheck) -> None:
    failure_count = register_failure(check.monitor_id)
    if failure_count is None:
        return

    incident, created = handle_incident(
        session,
        check.monitor_id,
        failure_count,
    )
    if created:
        send_incident_alert(incident)


def call_monitor_api_service(session, monitor_id: int) -> MonitorCheck:
    monitor = session.scalars(
        select(Monitor).where(Monitor.id == monitor_id)
    ).first()
    if monitor is None:
        raise HTTPException(status_code=404, detail="Monitor not found")

    start = time.perf_counter()
    try:
        response = requests.request(
            method=monitor.method,
            url=monitor.url,
            timeout=monitor.timeout_seconds,
        )
        latency_ms = (time.perf_counter() - start) * 1000
        status = (
            MonitorStatus.UP
            if response.status_code == monitor.expected_status
            else MonitorStatus.DOWN
        )
        check = _save_check(
            session,
            MonitorCheck(
                monitor_id=monitor.id,
                status=status,
                http_status=response.status_code,
                latency_ms=latency_ms,
            ),
        )
    except requests.RequestException as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        check = _save_check(
            session,
            MonitorCheck(
                monitor_id=monitor.id,
                status=MonitorStatus.DOWN,
                http_status=None,
                latency_ms=latency_ms,
                error_message=str(exc),
            ),
        )

    if check.status == MonitorStatus.DOWN:
        _process_failure(session, check)

    return check
