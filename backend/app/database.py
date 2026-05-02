from __future__ import annotations

import logging
import os
import sys
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

log = logging.getLogger(__name__)


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


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_conn, _):
    dbapi_conn.execute("PRAGMA journal_mode=WAL")
    dbapi_conn.execute("PRAGMA synchronous=NORMAL")


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]


def init_db() -> None:
    from backend.app import models  # noqa: F401 — ensures tables are registered
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL"))
    _migrate_columns()
    _seed_admin()
    _seed_config()


def _seed_config() -> None:
    from backend.app.models import GlobalConfig

    db = SessionLocal()
    try:
        if not db.get(GlobalConfig, 1):
            db.add(GlobalConfig(id=1, extra_hours_multiplier=1.5, standby_hours_multiplier=1.0))
            db.commit()
    finally:
        db.close()


def _seed_admin() -> None:
    import bcrypt as _bcrypt
    from backend.app.models import User

    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            db.add(User(
                username="admin",
                hashed_password=_bcrypt.hashpw(b"admin", _bcrypt.gensalt()).decode(),
                role="admin",
            ))
            db.commit()
            log.warning(
                "Utilizador 'admin' criado com password padrão. "
                "Altere imediatamente em produção."
            )
    finally:
        db.close()


def _migrate_columns() -> None:
    """Add columns introduced after the initial schema without dropping data."""
    from sqlalchemy import text
    try:
        with engine.begin() as conn:
            tr_cols = {row[1] for row in conn.execute(text("PRAGMA table_info(timesheet_record)"))}
            if "cost_per_hour" not in tr_cols:
                conn.execute(text(
                    "ALTER TABLE timesheet_record"
                    " ADD COLUMN cost_per_hour FLOAT NOT NULL DEFAULT 0.0"
                ))
            c_cols = {row[1] for row in conn.execute(text("PRAGMA table_info(collaborator)"))}
            if "seniority_level_id" not in c_cols:
                conn.execute(text(
                    "ALTER TABLE collaborator"
                    " ADD COLUMN seniority_level_id INTEGER REFERENCES seniority_level(id)"
                ))
            p_cols = {row[1] for row in conn.execute(text("PRAGMA table_info(project)"))}
            if "budget_cost" not in p_cols:
                conn.execute(text(
                    "ALTER TABLE project ADD COLUMN budget_cost FLOAT"
                ))
            cy_cols = {row[1] for row in conn.execute(text("PRAGMA table_info(cycle)"))}
            if "is_closed" not in cy_cols:
                conn.execute(text(
                    "ALTER TABLE cycle ADD COLUMN is_closed BOOLEAN NOT NULL DEFAULT 0"
                ))
            if "is_active" not in cy_cols:
                conn.execute(text(
                    "ALTER TABLE cycle ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1"
                ))
    except Exception:
        log.debug("_migrate_columns: erro ao migrar colunas", exc_info=True)
