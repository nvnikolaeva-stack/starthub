import uuid
from datetime import date, datetime, timedelta
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.constants import SPORT_TYPES


class EventBase(BaseModel):
    name: str = Field(..., max_length=512)
    date_start: date
    date_end: date | None = None
    location: str = Field(..., max_length=512)
    sport_type: str
    url: str | None = Field(None, max_length=2048)
    notes: str | None = None
    created_by: str = Field(..., max_length=512)

    @field_validator("sport_type")
    @classmethod
    def sport_type_must_be_known(cls, v: str) -> str:
        if v not in SPORT_TYPES:
            raise ValueError(f"sport_type must be one of: {', '.join(SPORT_TYPES)}")
        return v

    @model_validator(mode="after")
    def validate_dates(self) -> "EventBase":
        if self.date_end is not None:
            if self.date_end < self.date_start:
                raise ValueError("date_end must be on or after date_start")
            if self.date_end > self.date_start + timedelta(days=7):
                raise ValueError("date_end must be at most 7 days after date_start")
        return self


class EventCreate(EventBase):
    group_id: uuid.UUID | None = None


class EventUpdate(BaseModel):
    name: str | None = Field(None, max_length=512)
    date_start: date | None = None
    date_end: date | None = None
    location: str | None = Field(None, max_length=512)
    sport_type: str | None = None
    url: str | None = Field(None, max_length=2048)
    notes: str | None = None
    created_by: str | None = Field(None, max_length=512)
    group_id: uuid.UUID | None = None

    @field_validator("sport_type")
    @classmethod
    def sport_type_optional(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v not in SPORT_TYPES:
            raise ValueError(f"sport_type must be one of: {', '.join(SPORT_TYPES)}")
        return v


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    date_start: date
    date_end: date | None
    location: str
    sport_type: str
    url: str | None
    notes: str | None
    created_by: str
    created_at: datetime
    group_id: uuid.UUID | None = None
    group_name: str | None = None


class RegistrationWithParticipant(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_id: uuid.UUID
    participant_id: uuid.UUID
    distances: list[str]
    result_time: str | None
    result_place: str | None
    created_at: datetime
    participant_display_name: str
    participant_telegram_username: str | None
    participant_telegram_id: int | None = None


class EventDetail(EventRead):
    registrations: list[RegistrationWithParticipant]


class ParticipantBase(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=512)
    telegram_id: int | None = None
    telegram_username: str | None = Field(None, max_length=255)

    @field_validator("display_name")
    @classmethod
    def strip_display_name(cls, v: str) -> str:
        s = (v or "").strip()
        if not s:
            raise ValueError("display_name cannot be empty")
        return s


class ParticipantCreate(ParticipantBase):
    pass


class ParticipantUpdate(BaseModel):
    display_name: str | None = Field(None, max_length=512)
    telegram_id: int | None = None
    telegram_username: str | None = Field(None, max_length=255)


class ParticipantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    display_name: str
    telegram_id: int | None
    telegram_username: str | None
    normalized_name: str
    created_at: datetime


class ParticipantEventEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    registration_id: uuid.UUID
    event_id: uuid.UUID
    event_name: str
    date_start: date
    sport_type: str
    location: str
    distances: list[str]
    result_time: str | None
    result_place: str | None


class ParticipantDetail(ParticipantRead):
    events: list[ParticipantEventEntry]


class RegistrationCreate(BaseModel):
    event_id: uuid.UUID
    participant_id: uuid.UUID
    distances: list[str] = Field(default_factory=list)


class RegistrationUpdate(BaseModel):
    distances: list[str] | None = None
    result_time: str | None = Field(None, max_length=64)
    result_place: str | None = Field(None, max_length=128)


class RegistrationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_id: uuid.UUID
    participant_id: uuid.UUID
    distances: list[str]
    result_time: str | None
    result_place: str | None
    created_at: datetime


class ParticipantStats(BaseModel):
    total_events: int
    events_by_sport: dict[str, int]
    personal_records: dict[str, str]
    places_history: list[dict[str, Any]]


class MostActiveParticipant(BaseModel):
    participant_id: uuid.UUID
    display_name: str
    registrations_count: int


class CommunityStats(BaseModel):
    total_events: int
    total_participants: int
    most_active_participant: MostActiveParticipant | None
    popular_sports: list[dict[str, Any]]
    popular_locations: list[dict[str, Any]]


class GroupCreate(BaseModel):
    telegram_chat_id: int
    name: str | None = Field(None, max_length=512)


class GroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    telegram_chat_id: int
    name: str | None
    created_at: datetime


class GroupMemberEnsure(BaseModel):
    telegram_id: int
    display_name: str = Field(..., min_length=1, max_length=512)
    telegram_username: str | None = Field(None, max_length=255)

    @field_validator("display_name")
    @classmethod
    def strip_display_name(cls, v: str) -> str:
        s = (v or "").strip()
        if not s:
            raise ValueError("display_name cannot be empty")
        return s
