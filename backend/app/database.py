import os
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker


DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "timetrack.db"
DB_PATH = Path(os.getenv("TIMETRACK_DB_PATH", DEFAULT_DB_PATH))
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
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


def _ensure_columns():
    with engine.connect() as conn:
        columns = conn.exec_driver_sql("PRAGMA table_info(events);").fetchall()
        column_names = {col[1] for col in columns}
        if "is_private" not in column_names:
            conn.exec_driver_sql("ALTER TABLE events ADD COLUMN is_private BOOLEAN DEFAULT 0;")
