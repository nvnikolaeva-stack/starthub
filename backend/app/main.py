import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine

import app.models  # noqa: F401 — register models on Base.metadata

_DEFAULT_CORS = '["http://localhost:3000","http://127.0.0.1:3000"]'


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", _DEFAULT_CORS)
    try:
        data = json.loads(raw)
        if isinstance(data, list) and all(isinstance(x, str) for x in data):
            return data
    except json.JSONDecodeError:
        pass
    return ["http://localhost:3000", "http://127.0.0.1:3000"]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    from app.database import apply_sqlite_migrations  # noqa: PLC0415

    apply_sqlite_migrations()
    yield


app = FastAPI(title="#алкардио API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import events, groups, ocr, participants, registrations, stats  # noqa: E402

app.include_router(events.router, prefix="/api/v1")
app.include_router(groups.router, prefix="/api/v1")
app.include_router(ocr.router, prefix="/api/v1")
app.include_router(participants.router, prefix="/api/v1")
app.include_router(registrations.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")
