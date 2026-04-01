from __future__ import annotations

import uuid
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, not_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app import models
from app.constants import SPORT_TYPES
from app.schemas import (
    CommunityStats,
    EventCreate,
    EventDetail,
    EventRead,
    EventUpdate,
    GroupMemberEnsure,
    MostActiveParticipant,
    ParticipantCreate,
    ParticipantDetail,
    ParticipantEventEntry,
    ParticipantStats,
    ParticipantUpdate,
    RegistrationCreate,
    RegistrationUpdate,
    RegistrationWithParticipant,
    SimilarEventMatch,
)


def _weekend_range(today: date) -> tuple[date, date]:
    wd = today.weekday()
    if wd == 5:
        sat = today
    elif wd == 6:
        sat = today - timedelta(days=1)
    else:
        days_to_sat = (5 - wd) % 7
        if days_to_sat == 0:
            days_to_sat = 7
        sat = today + timedelta(days=days_to_sat)
    sun = sat + timedelta(days=1)
    return sat, sun


def _period_bounds(period: str, today: date) -> tuple[date | None, date | None]:
    if period == "all":
        return None, None
    if period == "weekend":
        return _weekend_range(today)
    if period == "month":
        return today, today + timedelta(days=30)
    if period == "3months":
        return today, today + timedelta(days=90)
    raise ValueError(f"Unknown period: {period}")


def get_group_ids_for_telegram(db: Session, telegram_id: int) -> list[uuid.UUID]:
    p = get_participant_by_telegram(db, telegram_id)
    if not p:
        return []
    return [g.id for g in p.groups]


def _apply_event_scope_for_list(
    q,
    db: Session,
    *,
    group_id: uuid.UUID | None,
    for_telegram_id: int | None,
):
    if group_id is not None:
        return q.filter(or_(models.Event.group_id == group_id, models.Event.group_id.is_(None)))
    if for_telegram_id is not None:
        gids = get_group_ids_for_telegram(db, for_telegram_id)
        if not gids:
            return q.filter(models.Event.group_id.is_(None))
        return q.filter(or_(models.Event.group_id.in_(gids), models.Event.group_id.is_(None)))
    return q


def _apply_event_date_filters(
    q,
    *,
    sport_type: str | None,
    upcoming: bool,
    limit: int,
    period: str,
    date_from: date | None = None,
    date_to: date | None = None,
):
    today = date.today()
    if sport_type:
        q = q.filter(models.Event.sport_type == sport_type)

    if date_from is not None:
        q = q.filter(models.Event.date_start >= date_from)
    elif upcoming:
        q = q.filter(models.Event.date_start >= today)

    if date_to is not None:
        q = q.filter(models.Event.date_start <= date_to)

    apply_period = date_from is None and date_to is None
    if apply_period:
        lo, hi = _period_bounds(period, today)
        if lo is not None and hi is not None:
            q = q.filter(
                models.Event.date_start >= lo,
                models.Event.date_start <= hi,
            )

    q = q.order_by(models.Event.date_start.asc())
    if limit > 0:
        q = q.limit(limit)
    return q


def list_events(
    db: Session,
    *,
    sport_type: str | None,
    upcoming: bool,
    limit: int,
    period: str,
    date_from: date | None = None,
    date_to: date | None = None,
    group_id: uuid.UUID | None = None,
    for_telegram_id: int | None = None,
) -> list[models.Event]:
    q = db.query(models.Event).options(joinedload(models.Event.group))
    q = _apply_event_scope_for_list(q, db, group_id=group_id, for_telegram_id=for_telegram_id)
    q = _apply_event_date_filters(
        q,
        sport_type=sport_type,
        upcoming=upcoming,
        limit=limit,
        period=period,
        date_from=date_from,
        date_to=date_to,
    )
    return list(q.all())


def list_events_strict_group(
    db: Session,
    group_uuid: uuid.UUID,
    *,
    sport_type: str | None,
    upcoming: bool,
    limit: int,
    period: str,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[models.Event]:
    q = (
        db.query(models.Event)
        .options(joinedload(models.Event.group))
        .filter(models.Event.group_id == group_uuid)
    )
    q = _apply_event_date_filters(
        q,
        sport_type=sport_type,
        upcoming=upcoming,
        limit=limit,
        period=period,
        date_from=date_from,
        date_to=date_to,
    )
    return list(q.all())


def get_event(db: Session, event_id: uuid.UUID) -> models.Event | None:
    return db.get(models.Event, event_id)


def get_event_with_registrations(db: Session, event_id: uuid.UUID) -> models.Event | None:
    return (
        db.query(models.Event)
        .options(
            joinedload(models.Event.group),
            joinedload(models.Event.registrations).joinedload(models.Registration.participant),
        )
        .filter(models.Event.id == event_id)
        .one_or_none()
    )


def create_event(db: Session, data: EventCreate) -> models.Event:
    ev = models.Event(
        name=data.name,
        date_start=data.date_start,
        date_end=data.date_end,
        location=data.location,
        sport_type=data.sport_type,
        url=data.url,
        notes=data.notes,
        created_by=data.created_by,
        group_id=data.group_id,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


def find_duplicate_event_by_name_date(
    db: Session, name: str, date_start: date
) -> models.Event | None:
    key = name.strip().lower()
    if not key:
        return None
    return (
        db.query(models.Event)
        .filter(
            func.lower(func.trim(models.Event.name)) == key,
            models.Event.date_start == date_start,
        )
        .first()
    )


def _event_covers_day(on_date: date):
    return or_(
        and_(
            models.Event.date_end.is_(None),
            models.Event.date_start == on_date,
        ),
        and_(
            models.Event.date_end.isnot(None),
            models.Event.date_start <= on_date,
            models.Event.date_end >= on_date,
        ),
    )


def _similar_base_query(db: Session):
    return db.query(models.Event).options(
        joinedload(models.Event.registrations).joinedload(
            models.Registration.participant
        ),
    )


def _filter_name_substr(q, name_substr: str):
    needle = name_substr.strip().lower()
    if not needle:
        return q
    return q.filter(func.instr(func.lower(models.Event.name), needle) > 0)


def _filter_date(q, on_date: date):
    return q.filter(_event_covers_day(on_date))


def event_to_similar_match(ev: models.Event) -> SimilarEventMatch:
    names: list[str] = []
    for r in ev.registrations or []:
        p = r.participant
        if p is not None and p.display_name:
            names.append(p.display_name)
    return SimilarEventMatch(
        id=ev.id,
        name=ev.name,
        date_start=ev.date_start,
        location=ev.location,
        sport_type=ev.sport_type,
        participants_count=len(names),
        participants=names,
    )


def search_similar_events(
    db: Session,
    *,
    name_substr: str | None,
    on_date: date | None,
) -> tuple[list[models.Event], list[models.Event]]:
    n = name_substr.strip() if name_substr else ""
    n = n or None

    if n and not on_date:
        rows = (
            _filter_name_substr(_similar_base_query(db), n)
            .order_by(models.Event.date_start)
            .limit(5)
            .all()
        )
        return rows, []

    if on_date and not n:
        rows = (
            _filter_date(_similar_base_query(db), on_date)
            .order_by(models.Event.date_start)
            .limit(5)
            .all()
        )
        return [], rows

    if on_date and n:
        q_all_date = _filter_date(_similar_base_query(db), on_date)
        exact_rows = (
            _filter_name_substr(
                _filter_date(_similar_base_query(db), on_date),
                n,
            )
            .order_by(models.Event.date_start)
            .limit(5)
            .all()
        )
        exact_ids = {e.id for e in exact_rows}
        rest_q = q_all_date
        if exact_ids:
            rest_q = rest_q.filter(not_(models.Event.id.in_(exact_ids)))
        date_rows = rest_q.order_by(models.Event.date_start).limit(5).all()
        return exact_rows, date_rows

    return [], []


def _validate_event_date_rule(date_start: date, date_end: date | None) -> None:
    if date_end is not None:
        if date_end < date_start:
            raise ValueError("date_end must be on or after date_start")
        if date_end > date_start + timedelta(days=7):
            raise ValueError("date_end must be at most 7 days after date_start")


def update_event(db: Session, event_id: uuid.UUID, data: EventUpdate) -> models.Event | None:
    ev = get_event(db, event_id)
    if not ev:
        return None

    updates = data.model_dump(exclude_unset=True)
    for key, val in updates.items():
        setattr(ev, key, val)

    _validate_event_date_rule(ev.date_start, ev.date_end)

    if ev.sport_type not in SPORT_TYPES:
        db.rollback()
        raise ValueError("invalid sport_type")

    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


def delete_event(db: Session, event_id: uuid.UUID) -> bool:
    ev = get_event(db, event_id)
    if not ev:
        return False
    db.delete(ev)
    db.commit()
    return True


def build_event_detail(ev: models.Event) -> EventDetail:
    regs: list[RegistrationWithParticipant] = []
    for r in ev.registrations:
        p = r.participant
        regs.append(
            RegistrationWithParticipant(
                id=r.id,
                event_id=r.event_id,
                participant_id=r.participant_id,
                distances=[str(x) for x in (r.distances or [])],
                result_time=r.result_time,
                result_place=r.result_place,
                created_at=r.created_at,
                participant_display_name=p.display_name,
                participant_telegram_username=p.telegram_username,
                participant_telegram_id=p.telegram_id,
            )
        )
    base = EventRead.model_validate(ev)
    return EventDetail(**base.model_dump(), registrations=regs)


def list_participants(db: Session) -> list[models.Participant]:
    return list(db.query(models.Participant).order_by(models.Participant.display_name.asc()).all())


def get_participant(db: Session, participant_id: uuid.UUID) -> models.Participant | None:
    return db.get(models.Participant, participant_id)


def get_participant_by_telegram(db: Session, telegram_id: int) -> models.Participant | None:
    return (
        db.query(models.Participant)
        .filter(models.Participant.telegram_id == telegram_id)
        .one_or_none()
    )


def get_upcoming_events_for_participant(
    db: Session,
    participant_id: uuid.UUID,
) -> list[models.Event]:
    today = date.today()
    return (
        db.query(models.Event)
        .join(models.Registration, models.Registration.event_id == models.Event.id)
        .filter(models.Registration.participant_id == participant_id)
        .filter(models.Event.date_start >= today)
        .order_by(models.Event.date_start.asc())
        .all()
    )


def get_participant_detail(db: Session, participant_id: uuid.UUID) -> ParticipantDetail | None:
    p = (
        db.query(models.Participant)
        .options(joinedload(models.Participant.registrations).joinedload(models.Registration.event))
        .filter(models.Participant.id == participant_id)
        .one_or_none()
    )
    if not p:
        return None
    events: list[ParticipantEventEntry] = []
    for reg in p.registrations:
        ev = reg.event
        events.append(
            ParticipantEventEntry(
                registration_id=reg.id,
                event_id=ev.id,
                event_name=ev.name,
                date_start=ev.date_start,
                sport_type=ev.sport_type,
                location=ev.location,
                distances=[str(x) for x in (reg.distances or [])],
                result_time=reg.result_time,
                result_place=reg.result_place,
            )
        )
    events.sort(key=lambda e: e.date_start)
    return ParticipantDetail(
        id=p.id,
        display_name=p.display_name,
        telegram_id=p.telegram_id,
        telegram_username=p.telegram_username,
        normalized_name=p.normalized_name,
        created_at=p.created_at,
        events=events,
    )


def create_or_get_participant(db: Session, data: ParticipantCreate) -> tuple[models.Participant, bool]:
    if data.telegram_id is not None:
        existing = get_participant_by_telegram(db, data.telegram_id)
        if existing:
            return existing, False

    norm = data.display_name.lower().strip()
    p = models.Participant(
        display_name=data.display_name,
        telegram_id=data.telegram_id,
        telegram_username=data.telegram_username,
        normalized_name=norm,
    )
    db.add(p)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if data.telegram_id is not None:
            existing = get_participant_by_telegram(db, data.telegram_id)
            if existing:
                return existing, False
        raise
    db.refresh(p)
    return p, True


def update_participant(
    db: Session,
    participant_id: uuid.UUID,
    data: ParticipantUpdate,
) -> models.Participant | None:
    p = get_participant(db, participant_id)
    if not p:
        return None
    updates = data.model_dump(exclude_unset=True)
    if "display_name" in updates and updates["display_name"] is not None:
        updates["normalized_name"] = updates["display_name"].lower().strip()
    for key, val in updates.items():
        setattr(p, key, val)
    db.add(p)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(p)
    return p


def create_registration(db: Session, data: RegistrationCreate) -> models.Registration:
    ev = get_event(db, data.event_id)
    if not ev:
        raise LookupError("event not found")
    p = get_participant(db, data.participant_id)
    if not p:
        raise LookupError("participant not found")

    reg = models.Registration(
        event_id=data.event_id,
        participant_id=data.participant_id,
        distances=list(data.distances),
    )
    db.add(reg)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise ValueError("duplicate registration for this event") from e
    db.refresh(reg)
    return reg


def get_registration(db: Session, registration_id: uuid.UUID) -> models.Registration | None:
    return db.get(models.Registration, registration_id)


def update_registration(
    db: Session,
    registration_id: uuid.UUID,
    data: RegistrationUpdate,
) -> models.Registration | None:
    r = get_registration(db, registration_id)
    if not r:
        return None
    updates = data.model_dump(exclude_unset=True)
    if "distances" in updates and updates["distances"] is not None:
        updates["distances"] = list(updates["distances"])
    for key, val in updates.items():
        setattr(r, key, val)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def delete_registration(db: Session, registration_id: uuid.UUID) -> bool:
    r = get_registration(db, registration_id)
    if not r:
        return False
    db.delete(r)
    db.commit()
    return True


def _parse_time_to_seconds(s: str | None) -> int | None:
    if not s or not str(s).strip():
        return None
    parts = str(s).strip().split(":")
    try:
        nums = [int(p) for p in parts]
    except ValueError:
        return None
    if len(nums) == 3:
        h, m, sec = nums
        return h * 3600 + m * 60 + sec
    if len(nums) == 2:
        m, sec = nums
        return m * 60 + sec
    if len(nums) == 1:
        return nums[0]
    return None


def get_participant_stats(db: Session, participant_id: uuid.UUID) -> ParticipantStats | None:
    p = get_participant(db, participant_id)
    if not p:
        return None

    regs = (
        db.query(models.Registration)
        .join(models.Event)
        .filter(models.Registration.participant_id == participant_id)
        .all()
    )

    total_events = len(regs)
    by_sport: Counter[str] = Counter()
    best_by_distance: dict[str, tuple[int, str]] = {}
    places_history: list[dict[str, Any]] = []

    for r in regs:
        ev = r.event
        by_sport[ev.sport_type] += 1
        if r.result_place:
            places_history.append(
                {
                    "event_name": ev.name,
                    "date_start": ev.date_start.isoformat(),
                    "result_place": r.result_place,
                    "sport_type": ev.sport_type,
                }
            )
        secs = _parse_time_to_seconds(r.result_time)
        if secs is None:
            continue
        for d in r.distances or []:
            label = str(d)
            prev = best_by_distance.get(label)
            if prev is None or secs < prev[0]:
                best_by_distance[label] = (secs, (r.result_time or "").strip())

    places_history.sort(key=lambda x: x["date_start"], reverse=True)

    return ParticipantStats(
        total_events=total_events,
        events_by_sport=dict(by_sport),
        personal_records={k: v[1] for k, v in best_by_distance.items()},
        places_history=places_history,
    )


def get_community_stats(
    db: Session,
    *,
    group_id: uuid.UUID | None = None,
    for_telegram_id: int | None = None,
) -> CommunityStats:
    q_ev = db.query(models.Event)
    if group_id is not None:
        q_ev = q_ev.filter(models.Event.group_id == group_id)
    elif for_telegram_id is not None:
        gids = get_group_ids_for_telegram(db, for_telegram_id)
        if not gids:
            q_ev = q_ev.filter(models.Event.group_id.is_(None))
        else:
            q_ev = q_ev.filter(
                or_(models.Event.group_id.in_(gids), models.Event.group_id.is_(None))
            )

    scoped_ids: list[uuid.UUID] = [r[0] for r in q_ev.with_entities(models.Event.id).all()]

    if not scoped_ids:
        return CommunityStats(
            total_events=0,
            total_participants=0,
            most_active_participant=None,
            popular_sports=[],
            popular_locations=[],
        )

    total_events = len(scoped_ids)

    total_participants = (
        db.query(func.count(func.distinct(models.Registration.participant_id)))
        .filter(models.Registration.event_id.in_(scoped_ids))
        .scalar()
    ) or 0

    rows = (
        db.query(
            models.Participant.id,
            models.Participant.display_name,
            func.count(models.Registration.id),
        )
        .join(models.Registration, models.Registration.participant_id == models.Participant.id)
        .filter(models.Registration.event_id.in_(scoped_ids))
        .group_by(models.Participant.id, models.Participant.display_name)
        .all()
    )
    best_row: tuple[Any, ...] | None = None
    for row in rows:
        if best_row is None or row[2] > best_row[2]:
            best_row = row

    most_active: MostActiveParticipant | None = None
    if best_row and best_row[2] and best_row[2] > 0:
        most_active = MostActiveParticipant(
            participant_id=best_row[0],
            display_name=best_row[1],
            registrations_count=best_row[2],
        )

    sport_rows = (
        db.query(models.Event.sport_type, func.count(models.Event.id))
        .filter(models.Event.id.in_(scoped_ids))
        .group_by(models.Event.sport_type)
        .order_by(func.count(models.Event.id).desc())
        .all()
    )
    popular_sports = [{"sport_type": r[0], "count": r[1]} for r in sport_rows]

    loc_rows = (
        db.query(models.Event.location, func.count(models.Event.id))
        .filter(models.Event.id.in_(scoped_ids))
        .group_by(models.Event.location)
        .order_by(func.count(models.Event.id).desc())
        .limit(10)
        .all()
    )
    popular_locations = [{"location": r[0], "count": r[1]} for r in loc_rows]

    return CommunityStats(
        total_events=int(total_events),
        total_participants=int(total_participants),
        most_active_participant=most_active,
        popular_sports=popular_sports,
        popular_locations=popular_locations,
    )


def list_groups(db: Session) -> list[models.Group]:
    return list(db.query(models.Group).order_by(models.Group.created_at.asc()).all())


def upsert_group(
    db: Session, telegram_chat_id: int, name: str | None
) -> tuple[models.Group, bool]:
    g = (
        db.query(models.Group)
        .filter(models.Group.telegram_chat_id == telegram_chat_id)
        .one_or_none()
    )
    if g:
        if name and g.name != name:
            g.name = name
            db.add(g)
            db.commit()
            db.refresh(g)
        return g, False
    g = models.Group(telegram_chat_id=telegram_chat_id, name=name)
    db.add(g)
    db.commit()
    db.refresh(g)
    return g, True


def get_group_by_telegram(db: Session, telegram_chat_id: int) -> models.Group | None:
    return (
        db.query(models.Group)
        .filter(models.Group.telegram_chat_id == telegram_chat_id)
        .one_or_none()
    )


def get_group_row(db: Session, group_id: uuid.UUID) -> models.Group | None:
    return db.get(models.Group, group_id)


def ensure_group_member(
    db: Session, group_id: uuid.UUID, body: GroupMemberEnsure
) -> models.Participant:
    g = get_group_row(db, group_id)
    if not g:
        raise LookupError("group not found")
    payload = ParticipantCreate(
        display_name=body.display_name,
        telegram_id=body.telegram_id,
        telegram_username=body.telegram_username,
    )
    p, _created = create_or_get_participant(db, payload)
    if g not in p.groups:
        p.groups.append(g)
        db.add(p)
        db.commit()
        db.refresh(p)
    return p


def groups_for_telegram_participant(db: Session, telegram_id: int) -> list[models.Group]:
    p = get_participant_by_telegram(db, telegram_id)
    if not p:
        return []
    return list(p.groups)


def list_participants_for_group(db: Session, group_id: uuid.UUID) -> list[models.Participant]:
    g = get_group_row(db, group_id)
    if not g:
        return []
    return list(g.participants)
