import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

_backend_dir = Path(__file__).resolve().parent.parent

if os.environ.get("STARTHUB_TESTING") == "1":
    _db_file = _backend_dir / "test_starthub.db"
    DATABASE_URL = f"sqlite:///{_db_file}"
else:
    _default_sqlite = f"sqlite:///{_backend_dir / 'starthub.db'}"
    DATABASE_URL = os.getenv("DATABASE_URL", _default_sqlite)

_engine_kwargs: dict = {}
if DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **_engine_kwargs)

Base = declarative_base()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _connection_record):
    if not DATABASE_URL.startswith("sqlite"):
        return
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def apply_sqlite_migrations() -> None:
    """Добавляет колонки к существующей SQLite БД после обновления кода."""
    if not DATABASE_URL.startswith("sqlite"):
        return
    with engine.begin() as conn:
        r = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
        )
        if r.fetchone() is None:
            return
        r2 = conn.execute(text("PRAGMA table_info(events)"))
        cols = {row[1] for row in r2.fetchall()}
        if "group_id" not in cols:
            conn.execute(
                text("ALTER TABLE events ADD COLUMN group_id TEXT REFERENCES groups(id)")
            )
