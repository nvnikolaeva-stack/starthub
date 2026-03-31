import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import EventRead, GroupCreate, GroupMemberEnsure, GroupRead, ParticipantRead

router = APIRouter(prefix="/groups", tags=["groups"])

PeriodLiteral = Literal["weekend", "month", "3months", "all"]


@router.post("", response_model=GroupRead)
def create_group(payload: GroupCreate, db: Annotated[Session, Depends(get_db)]):
    g, _created = crud.upsert_group(
        db, telegram_chat_id=payload.telegram_chat_id, name=payload.name
    )
    return g


@router.get("/by-telegram/{telegram_chat_id}", response_model=GroupRead)
def get_group_by_telegram_route(
    telegram_chat_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    g = crud.get_group_by_telegram(db, telegram_chat_id)
    if not g:
        raise HTTPException(status_code=404, detail="Group not found")
    return g


@router.get("", response_model=list[GroupRead])
def list_all_groups(db: Annotated[Session, Depends(get_db)]):
    return crud.list_groups(db)


@router.get("/{group_id}/events", response_model=list[EventRead])
def list_group_events(
    group_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    sport_type: str | None = None,
    upcoming: bool = True,
    limit: int = Query(default=5, ge=1, le=500),
    period: PeriodLiteral = "all",
):
    if not crud.get_group_row(db, group_id):
        raise HTTPException(status_code=404, detail="Group not found")
    try:
        return crud.list_events_strict_group(
            db,
            group_id,
            sport_type=sport_type,
            upcoming=upcoming,
            limit=limit,
            period=period,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{group_id}/stats")
def group_stats(group_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]):
    if not crud.get_group_row(db, group_id):
        raise HTTPException(status_code=404, detail="Group not found")
    return crud.get_community_stats(db, group_id=group_id)


@router.get("/{group_id}/participants", response_model=list[ParticipantRead])
def group_participants(group_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]):
    if not crud.get_group_row(db, group_id):
        raise HTTPException(status_code=404, detail="Group not found")
    parts = crud.list_participants_for_group(db, group_id)
    return parts


@router.post("/{group_id}/ensure-member", response_model=ParticipantRead, status_code=200)
def ensure_group_member_route(
    group_id: uuid.UUID,
    payload: GroupMemberEnsure,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        p = crud.ensure_group_member(db, group_id, payload)
    except LookupError:
        raise HTTPException(status_code=404, detail="Group not found") from None
    return p
