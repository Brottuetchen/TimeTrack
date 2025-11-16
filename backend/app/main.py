import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .bluetooth_agent import start_agent
from .routers import assignments, bluetooth, calls, events, export, imports, milestones, projects, sessions, rules, settings

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("timetrack-main")

init_db()
start_agent()
LOGGER.info("Bluetooth agent bootstrap triggered")

app = FastAPI(title="TimeTrack MVP", version="0.1.0")


# Performance monitoring middleware
@app.middleware("http")
async def log_slow_requests(request: Request, call_next):
    """
    Log requests that take longer than 500ms.
    Helps identify performance bottlenecks on Raspberry Pi.
    """
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    # Log slow requests for performance monitoring
    if duration > 0.5:
        LOGGER.warning(
            f"Slow request: {request.method} {request.url.path} took {duration:.2f}s"
        )

    # Add performance header for debugging
    response.headers["X-Process-Time"] = f"{duration:.3f}"

    return response


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
app.include_router(sessions.router)
app.include_router(rules.router)
app.include_router(export.router)
app.include_router(settings.router)
app.include_router(bluetooth.router)
app.include_router(imports.router)
app.include_router(calls.router)


@app.get("/health")
def healthcheck():
    return {"status": "ok"}
