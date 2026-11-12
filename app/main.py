from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .schemas import Auth, EventResponse, MonitorCreate, MonitorResponse, MonitorCheckResponse
from .database import get_db
from .utils import add_record, fetch_data
from traceback import format_exc
from .services.monitor_service import create_monitior_service
from .services.monitor_api_service import call_monitor_api_service


app = FastAPI()


@app.get("/health")
def health_check():
    return {
        "message": "Hello World"
    }

@app.post("/events", response_model = EventResponse, status_code = 201)
def events_api(req: Auth, db: Session = Depends(get_db)):
    print("data", req, req.message, "--------------------------------")
    response = add_record(db, req)
    # print("resp", resp)
    return response


@app.get("/events")
def events_api(db: Session = Depends(get_db)):
    
    resp = fetch_data(db)
    return resp

@app.post('/monitor', response_model = MonitorResponse, status_code=201)
def execute_monitor_api(req: MonitorCreate, session: Session = Depends(get_db)):
    try:
        print("STARTED")
        return create_monitior_service(req, session)
    except Exception as e:
        print(f"Error in execute_monitor_api func {format_exc()}")


@app.post('/monitor/{monitor_id}/check', response_model=MonitorCheckResponse) # 
def monitor_api_check(monitor_id: int, session: Session = Depends(get_db)):
    try:
        resp = call_monitor_api_service(session, monitor_id)
        return resp
    except Exception as e:
        print(e)