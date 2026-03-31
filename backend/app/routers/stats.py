import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.constants import DISTANCES, SPORT_TYPES
from app.database import get_db
from app.schemas import CommunityStats, ParticipantStats

router = APIRouter(tags=["stats"])


@router.get("/stats/participant/{participant_id}", response_model=ParticipantStats)
def participant_stats(
    participant_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
):
    stats = crud.get_participant_stats(db, participant_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Participant not found")
    return stats


@router.get("/stats/community", response_model=CommunityStats)
def community_stats(
    db: Annotated[Session, Depends(get_db)],
    group_id: uuid.UUID | None = None,
    for_telegram_id: int | None = None,
):
    return crud.get_community_stats(
        db, group_id=group_id, for_telegram_id=for_telegram_id
    )


@router.get("/distances/{sport_type}")
def distances_for_sport(sport_type: str):
    if sport_type not in SPORT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"sport_type must be one of: {', '.join(SPORT_TYPES)}",
        )
    return {"sport_type": sport_type, "distances": DISTANCES.get(sport_type, [])}
