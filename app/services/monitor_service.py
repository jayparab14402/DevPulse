from ..models import Monitor, MonitorCheck
from sqlalchemy import Select

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
    query = Select(Monitor).where(Monitor.id == ref_id)
    sess_query = session.scalars(query).first()
    print(sess_query)
    return sess_query


def create_monitior_service(req, session):
    try:
        print("INSIDE create_monitior_service")
        body = Monitor(
            name=req.name,
            url=req.url,
            method=req.method,
            expected_status=req.expected_status,
            timeout_seconds=req.timeout_seconds
        )
        session.add(body)
        print("ADDED")

        session.commit()
        print("COMMITED")

        session.refresh(body)
        print("REFRESHED")
        return get_monitor_rec(session, body.id)
    except Exception as e:
        session.rollback()
        print("Error", e)

