import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import RegistrationCreate, RegistrationRead, RegistrationUpdate

router = APIRouter(prefix="/registrations", tags=["registrations"])


@router.post("", response_model=RegistrationRead, status_code=201)
def create_registration(
    payload: RegistrationCreate,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        r = crud.create_registration(db, payload)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return r


@router.put("/{registration_id}", response_model=RegistrationRead)
def update_registration(
    registration_id: uuid.UUID,
    payload: RegistrationUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    r = crud.update_registration(db, registration_id, payload)
    if not r:
        raise HTTPException(status_code=404, detail="Registration not found")
    return r


@router.delete("/{registration_id}", status_code=204)
def delete_registration(
    registration_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
):
    if not crud.delete_registration(db, registration_id):
        raise HTTPException(status_code=404, detail="Registration not found")
    return Response(status_code=204)
