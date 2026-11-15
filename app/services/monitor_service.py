from sqlalchemy import select

from ..models import Monitor

'''
{
  "name": "GitHub API",
  "url": "https://api.github.com/repos/octocat/Hello-World",
  "method": "GET",
  "expected_status": 200,
  "timeout_seconds": 5
}
'''
def get_monitor_rec(session, ref_id):
    query = select(Monitor).where(Monitor.id == ref_id)
    return session.scalars(query).first()


def create_monitior_service(req, session):
    try:
        body = Monitor(
            name=req.name,
            url=req.url,
            method=req.method,
            expected_status=req.expected_status,
            timeout_seconds=req.timeout_seconds
        )
        session.add(body)
        session.commit()
        session.refresh(body)
        return get_monitor_rec(session, body.id)
    except Exception:
        session.rollback()
        raise

