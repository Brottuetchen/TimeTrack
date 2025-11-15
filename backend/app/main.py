import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .bluetooth_agent import start_agent
from .routers import assignments, bluetooth, calls, events, export, imports, milestones, projects, settings

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("timetrack-main")

init_db()
start_agent()
LOGGER.info("Bluetooth agent bootstrap triggered")

app = FastAPI(title="TimeTrack MVP", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router)
app.include_router(projects.router)
app.include_router(milestones.router)
app.include_router(assignments.router)
app.include_router(export.router)
app.include_router(settings.router)
app.include_router(bluetooth.router)
app.include_router(imports.router)
app.include_router(calls.router)


@app.get("/health")
def healthcheck():
    return {"status": "ok"}
