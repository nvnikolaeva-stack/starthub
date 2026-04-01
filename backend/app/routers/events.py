import uuid
from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app import crud, models
from app.database import get_db
from app.ical_utils import build_ical_calendar
from app.schemas import (
    EventCreate,
    EventDetail,
    EventRead,
    EventUpdate,
    SimilarEventsResponse,
)

router = APIRouter(prefix="/events", tags=["events"])

PeriodLiteral = Literal["weekend", "month", "3months", "all"]


@router.get("", response_model=list[EventRead])
def list_events(
    db: Annotated[Session, Depends(get_db)],
    sport_type: str | None = None,
    upcoming: bool = True,
    limit: int = Query(default=5, ge=1, le=500),
    period: PeriodLiteral = "all",
    date_from: date | None = None,
    date_to: date | None = None,
    group_id: uuid.UUID | None = None,
    for_telegram_id: int | None = None,
):
    try:
        return crud.list_events(
            db,
            sport_type=sport_type,
            upcoming=upcoming,
            limit=limit,
            period=period,
            date_from=date_from,
            date_to=date_to,
            group_id=group_id,
            for_telegram_id=for_telegram_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/search/similar", response_model=SimilarEventsResponse)
def search_similar_events(
    db: Annotated[Session, Depends(get_db)],
    name: str | None = None,
    event_date: date | None = Query(None, alias="date"),
):
    n = (name or "").strip() or None
    if not n and not event_date:
        return SimilarEventsResponse(exact_matches=[], date_matches=[])
    ex, dm = crud.search_similar_events(db, name_substr=n, on_date=event_date)
    return SimilarEventsResponse(
        exact_matches=[crud.event_to_similar_match(e) for e in ex],
        date_matches=[crud.event_to_similar_match(e) for e in dm],
    )


@router.get("/{event_id}", response_model=EventDetail)
def get_event(event_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]):
    ev = crud.get_event_with_registrations(db, event_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    return crud.build_event_detail(ev)


@router.post("", response_model=EventRead, status_code=201)
def create_event(
    payload: EventCreate,
    db: Annotated[Session, Depends(get_db)],
    x_force_create: Annotated[str | None, Header()] = None,
):
    force = (x_force_create or "").lower() in ("true", "1", "yes")
    if not force:
        dup = crud.find_duplicate_event_by_name_date(
            db, payload.name, payload.date_start
        )
        if dup:
            return JSONResponse(
                status_code=409,
                content={
                    "detail": "duplicate_event",
                    "existing_event_id": str(dup.id),
                    "message": "Старт с таким названием и датой уже существует",
                },
            )
    ev = crud.create_event(db, payload)
    return ev


@router.put("/{event_id}", response_model=EventRead)
def update_event(
    event_id: uuid.UUID,
    payload: EventUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        ev = crud.update_event(db, event_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    return ev


@router.delete("/{event_id}", status_code=204)
def delete_event(event_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]):
    if not crud.delete_event(db, event_id):
        raise HTTPException(status_code=404, detail="Event not found")
    return Response(status_code=204)


@router.get("/{event_id}/ical")
def get_event_ical(event_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]):
    ev = crud.get_event(db, event_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")

    body = build_ical_calendar(ev)
    filename = f"alkardio-event-{ev.id}.ics"
    return Response(
        content=body,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
