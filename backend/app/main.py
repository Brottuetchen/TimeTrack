from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers import assignments, events, export, imports, milestones, projects

init_db()

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
app.include_router(imports.router)


@app.get("/health")
def healthcheck():
    return {"status": "ok"}
