import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.ical_utils import build_combined_ical_calendar
from app.schemas import GroupRead, ParticipantCreate, ParticipantDetail, ParticipantRead, ParticipantUpdate

router = APIRouter(prefix="/participants", tags=["participants"])


@router.get("", response_model=list[ParticipantRead])
def list_participants(db: Annotated[Session, Depends(get_db)]):
    return crud.list_participants(db)


@router.get("/by-telegram/{telegram_id}/groups", response_model=list[GroupRead])
def list_groups_for_telegram_user(
    telegram_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    return crud.groups_for_telegram_participant(db, telegram_id)


@router.get("/by-telegram/{telegram_id}", response_model=ParticipantRead)
def get_participant_by_telegram_route(
    telegram_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    p = crud.get_participant_by_telegram(db, telegram_id)
    if not p:
        raise HTTPException(status_code=404, detail="Participant not found")
    return p


@router.get("/by-telegram/{telegram_id}/ical")
def get_participant_ical_combined(
    telegram_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    p = crud.get_participant_by_telegram(db, telegram_id)
    if not p:
        raise HTTPException(status_code=404, detail="Participant not found")
    evs = crud.get_upcoming_events_for_participant(db, p.id)
    body = build_combined_ical_calendar(evs)
    filename = f"alkardio-my-starts-{telegram_id}.ics"
    return Response(
        content=body,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{participant_id}", response_model=ParticipantDetail)
def get_participant(participant_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]):
    detail = crud.get_participant_detail(db, participant_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Participant not found")
    return detail


@router.post("", response_model=ParticipantRead, status_code=201)
def create_participant(payload: ParticipantCreate, db: Annotated[Session, Depends(get_db)]):
    p, _created = crud.create_or_get_participant(db, payload)
    return p


@router.put("/{participant_id}", response_model=ParticipantRead)
def update_participant(
    participant_id: uuid.UUID,
    payload: ParticipantUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        p = crud.update_participant(db, participant_id, payload)
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Telegram ID already linked to another participant",
        ) from None
    if not p:
        raise HTTPException(status_code=404, detail="Participant not found")
    return p
