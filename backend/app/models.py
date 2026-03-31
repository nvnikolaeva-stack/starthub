import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.database import Base


participant_group_link = Table(
    "participant_groups",
    Base.metadata,
    Column("participant_id", Uuid(as_uuid=True), ForeignKey("participants.id", ondelete="CASCADE"), primary_key=True),
    Column("group_id", Uuid(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
)


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=lambda: datetime.utcnow(),
    )

    events: Mapped[list["Event"]] = relationship("Event", back_populates="group")
    participants: Mapped[list["Participant"]] = relationship(
        "Participant",
        secondary=participant_group_link,
        back_populates="groups",
    )


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    date_start: Mapped[date] = mapped_column(Date, nullable=False)
    date_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    location: Mapped[str] = mapped_column(String(512), nullable=False)
    sport_type: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=lambda: datetime.utcnow(),
    )
    group_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("groups.id", ondelete="SET NULL"),
        nullable=True,
    )

    group: Mapped["Group | None"] = relationship("Group", back_populates="events")
    registrations: Mapped[list["Registration"]] = relationship(
        "Registration",
        back_populates="event",
        cascade="all, delete-orphan",
    )

    @property
    def group_name(self) -> str | None:
        if self.group_id is None:
            return None
        g = self.group
        return g.name if g is not None else None


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    display_name: Mapped[str] = mapped_column(String(512), nullable=False)
    telegram_id: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True)
    telegram_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    normalized_name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=lambda: datetime.utcnow(),
    )

    registrations: Mapped[list["Registration"]] = relationship(
        "Registration",
        back_populates="participant",
    )
    groups: Mapped[list["Group"]] = relationship(
        "Group",
        secondary=participant_group_link,
        back_populates="participants",
    )


class Registration(Base):
    __tablename__ = "registrations"
    __table_args__ = (
        UniqueConstraint("event_id", "participant_id", name="uq_registration_event_participant"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )
    participant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("participants.id"),
        nullable=False,
    )
    distances: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: [],
    )
    result_time: Mapped[str | None] = mapped_column(String(64), nullable=True)
    result_place: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=lambda: datetime.utcnow(),
    )

    event: Mapped["Event"] = relationship("Event", back_populates="registrations")
    participant: Mapped["Participant"] = relationship("Participant", back_populates="registrations")
