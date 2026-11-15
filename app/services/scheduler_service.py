import os

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select

from ..database import SessionLocal
from ..models import Monitor
from .monitor_api_service import call_monitor_api_service


MONITOR_INTERVAL_SECONDS = int(os.getenv("MONITOR_INTERVAL_SECONDS", "60"))

scheduler = BackgroundScheduler(timezone="UTC")


def monitor_job() -> None:
    session = SessionLocal()
    try:
        monitors = session.scalars(
            select(Monitor).where(Monitor.enabled.is_(True))
        ).all()
        for monitor in monitors:
            try:
                call_monitor_api_service(session, monitor.id)
            except Exception as exc:
                session.rollback()
                print(f"Scheduled check failed for monitor {monitor.id}: {exc}")
    finally:
        session.close()


def start_scheduler() -> None:
    if scheduler.running:
        return
    if scheduler.get_job("monitor-checks") is None:
        scheduler.add_job(
            monitor_job,
            "interval",
            seconds=MONITOR_INTERVAL_SECONDS,
            id="monitor-checks",
            max_instances=1,
            coalesce=True,
        )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
