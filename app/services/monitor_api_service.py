
from traceback import format_exc
from sqlalchemy import Select
from ..models import Monitor, MonitorCheck
import requests
import time
from fastapi import HTTPException
from ..redis_client import register_failure

def call_monitor_api_service(session, ref_id):

    try:
        obj = Select(Monitor).where(Monitor.id == ref_id)
        query = session.scalars(obj).first()
        if not query:
            raise HTTPException(
                status_code=404,
                detail="Monitor not found"
            )
        db_url = query.url
        db_timeout = query.timeout_seconds

        start = time.perf_counter()
        call = requests.get(url=db_url, timeout=db_timeout)
        end = time.perf_counter()
        elapsed_time = (end - start) * 1000
        elapsed_time_in_ms = elapsed_time
        resp = call.json()
        resp_status_code = call.status_code
        data = MonitorCheck(
            monitor_id = query.id,
            status = "UP" if resp_status_code == query.expected_status else "DOWN",
            http_status = resp_status_code,
            latency_ms = elapsed_time_in_ms,    
        )
        session.add(data)
        session.commit()
        session.refresh(data)
        print(f"((((((((((((((((((((({data.status})))))))))))))))))))))")

        if data.status != "UP":
            register_failure(data.monitor_id)
        return {
            "id": data.id,
            "monitor_id": data.monitor_id,
            "status": data.status,
            "http_status": data.http_status,
            "latency_ms": data.latency_ms,
            "error_message": data.error_message,
            "checked_at": data.checked_at

        }
        # print("--------------------------------------------------", data)
    except requests.RequestException as e:
        elapsed_time_ms = (time.perf_counter() - start) * 1000

        data = MonitorCheck(
            monitor_id=query.id,
            status="DOWN",
            http_status=None,
            latency_ms=elapsed_time_ms,
            error_message=str(e)
        )
        register_failure(data.monitor_id)

        session.add(data)
        session.commit()
        session.refresh(data)

        return data
    
    except Exception as e:
        return {
                    "id": data.id,
                    "monitor_id": data.monitor_id,
                    "status": None,
                    "http_status": None,
                    "latency_ms": data.latency_ms,
                    "error_message": str(e),
                    "checked_at": data.checked_at
        
                }
        print(f"Error in call_monitor_api_service {e}")

