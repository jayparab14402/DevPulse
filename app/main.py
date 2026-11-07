from fastapi import FastAPI
from .schemas import Auth


app = FastAPI()


@app.get("/health")
def health_check():
    return {
        "OK"
    }

@app.post("/events")
def events_api(req: Auth):
    return {"res": req}