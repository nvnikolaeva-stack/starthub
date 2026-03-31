"""Генерация .ics (RFC 5545, целый день) для событий."""

from __future__ import annotations

from datetime import datetime, timedelta

from app import models


def ics_escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )


def vevent_lines(ev: models.Event) -> list[str]:
    uid = f"{ev.id}@alkardio.local"
    dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dstart = ev.date_start.strftime("%Y%m%d")
    end_exclusive = (ev.date_end or ev.date_start) + timedelta(days=1)
    dend = end_exclusive.strftime("%Y%m%d")
    summary = ics_escape(ev.name)
    location = ics_escape(ev.location)
    desc = ics_escape(ev.notes or "") if ev.notes else ""
    url_line = ev.url.strip() if ev.url else ""

    lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART;VALUE=DATE:{dstart}",
        f"DTEND;VALUE=DATE:{dend}",
        f"SUMMARY:{summary}",
        f"LOCATION:{location}",
    ]
    if desc:
        lines.append(f"DESCRIPTION:{desc}")
    if url_line:
        lines.append(f"URL:{url_line}")
    lines.append("END:VEVENT")
    return lines


def build_ical_calendar(ev: models.Event) -> str:
    head = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//alkardio//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    tail = ["END:VCALENDAR"]
    return "\r\n".join(head + vevent_lines(ev) + tail) + "\r\n"


def build_combined_ical_calendar(events: list[models.Event]) -> str:
    head = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//alkardio//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    body: list[str] = []
    for ev in events:
        body.extend(vevent_lines(ev))
    tail = ["END:VCALENDAR"]
    return "\r\n".join(head + body + tail) + "\r\n"
