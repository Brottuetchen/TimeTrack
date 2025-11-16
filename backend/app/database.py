import os
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool


DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "timetrack.db"
DB_PATH = Path(os.getenv("TIMETRACK_DB_PATH", DEFAULT_DB_PATH))
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # SQLite-optimized connection pooling
    echo=False,  # Disable SQL logging in production for performance
)


# Configure SQLite for optimal performance on Raspberry Pi
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    Sets SQLite pragmas for better performance:
    - WAL mode: Better concurrency (multiple readers + 1 writer)
    - NORMAL synchronous: Faster writes (safe for Pi with stable power)
    - Larger cache: 10MB cache in memory
    - Memory temp store: Faster temp operations
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-10000")  # 10MB cache (negative = KB)
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.execute("PRAGMA mmap_size=268435456")  # 256MB memory-mapped I/O
    cursor.close()


SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)

Base = declarative_base()


@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_db():
    with get_session() as session:
        yield session


def init_db():
    """Create all tables. Call during startup for MVP deployment."""
    from . import models  # noqa: F401  # Import for side effects

    Base.metadata.create_all(bind=engine)
    _ensure_columns()
    _run_data_migrations()


def _ensure_columns():
    with engine.connect() as conn:
        columns = conn.exec_driver_sql("PRAGMA table_info(events);").fetchall()
        column_names = {col[1] for col in columns}
        if "is_private" not in column_names:
            conn.exec_driver_sql("ALTER TABLE events ADD COLUMN is_private BOOLEAN DEFAULT 0;")


def _run_data_migrations():
    """Run data migrations after schema is created."""
    from .migrations import auto_migrate_on_startup

    with get_session() as session:
        auto_migrate_on_startup(session)
