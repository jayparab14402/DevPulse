from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .schemas import Auth, EventResponse
from .database import get_db
from .utils import add_record, fetch_data


app = FastAPI()


@app.get("/health")
def health_check():
    return {
        "OK"
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