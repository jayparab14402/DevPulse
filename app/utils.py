from sqlalchemy import select

from .models import ErrorEvent


def fetch_data(session):
    return session.scalars(select(ErrorEvent)).all()


def add_record(session, data):
    try:
        event = ErrorEvent(
            service=data.service,
            level=data.level,
            message=data.message,
            status_code=data.status_code,
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        return event
    except Exception:
        session.rollback()
        raise
