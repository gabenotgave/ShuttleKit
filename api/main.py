import json
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ShuttleKit API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def load_config() -> dict:
    path = Path(__file__).parent / "config.json"
    with open(path) as f:
        return json.load(f)


@app.get("/api/stops")
def get_stops():
    pass


@app.get("/api/routes")
def get_routes():
    pass


@app.get("/api/status")
def get_status():
    pass


@app.get("/api/plan")
def get_plan(
    from_stop: str = Query(..., alias="from"),
    to_stop: str = Query(..., alias="to"),
    time: str = Query(default=None, description="HH:MM — defaults to now"),
):
    pass