from __future__ import annotations

import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


def _db_path() -> str:
    # When frozen (PyInstaller), store next to the executable so the file persists.
    # In development, use the project root (same original behaviour).
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, "pmas.db")


DATABASE_URL = f"sqlite:///{_db_path()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from backend.app import models  # noqa: F401 — ensures tables are registered
    Base.metadata.create_all(bind=engine)
    _migrate_columns()


def _migrate_columns() -> None:
    """Add columns introduced after the initial schema without dropping data."""
    from sqlalchemy import text
    try:
        with engine.begin() as conn:
            result = conn.execute(text("PRAGMA table_info(timesheet_record)"))
            existing = {row[1] for row in result}
            if "cost_per_hour" not in existing:
                conn.execute(text(
                    "ALTER TABLE timesheet_record"
                    " ADD COLUMN cost_per_hour FLOAT NOT NULL DEFAULT 0.0"
                ))
    except Exception:
        pass  # table not yet created; create_all handles that
