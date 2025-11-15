#!/usr/bin/env python3
"""
Seed the TimeTrack backend with dummy data for demos/tests.

Usage:
    python scripts/seed_dummy_data.py --base-url http://localhost:8000

API must be reachable (docker compose up).
"""

from __future__ import annotations

import argparse
import datetime as dt
import random
from typing import Dict, List

import requests


PROJECTS = [
    {"name": "Projekt A – Neubau Halle", "kunde": "Kunde Müller", "notizen": "Statik & Ausführungsplanung"},
    {"name": "Projekt B – Büroausbau", "kunde": "Kunde Schulz", "notizen": "Innenausbau / TGA"},
]

MILESTONES = [
    {"project": "Projekt A – Neubau Halle", "name": "LPH 1-3", "soll_stunden": 120, "ist_stunden": 86, "bonus_relevant": False},
    {"project": "Projekt A – Neubau Halle", "name": "LPH 5", "soll_stunden": 160, "ist_stunden": 40, "bonus_relevant": True},
    {"project": "Projekt B – Büroausbau", "name": "Entwurf", "soll_stunden": 80, "ist_stunden": 55, "bonus_relevant": False},
]

WINDOW_TEMPLATES = [
    {"window_title": "AutoCAD – Werkhalle_Stahlbau.dwg", "process_name": "acad.exe"},
    {"window_title": "Revit – Büroausbau.rvt", "process_name": "revit.exe"},
    {"window_title": "Word – Baustellenprotokoll.docx", "process_name": "winword.exe"},
    {"window_title": "Excel – Leistungsnachweis.xlsx", "process_name": "excel.exe"},
    {"window_title": "Outlook – Kundenmail", "process_name": "outlook.exe"},
]

PHONE_CONTACTS = [
    ("+491701234567", "Bauleitung Müller", "OUTGOING"),
    ("+491761112233", "Statikerin Schulze", "OUTGOING"),
    ("+49891234567", "Kunde Schulz", "INCOMING"),
    ("+491512223344", "Lieferant Stahlbau", "OUTGOING"),
]

ACTIVITIES = ["Planung", "Baustelle", "Dokumentation", "Meeting", "Fahrt", "Telefon", "PC"]


def iso(hours_ago: float) -> dt.datetime:
    return (dt.datetime.utcnow() - dt.timedelta(hours=hours_ago)).replace(microsecond=0)


def generate_window_events(days: int, per_day: int) -> List[dict]:
    events = []
    for day in range(days):
        base_hours = 24 * day
        for idx in range(per_day):
            template = random.choice(WINDOW_TEMPLATES)
            start_offset = base_hours + random.randint(1, 10) + idx * 2
            duration = random.randint(10, 60)
            events.append({
                "timestamp_start": -start_offset,
                "duration": duration,
                "window_title": template["window_title"],
                "process_name": template["process_name"],
            })
    return events


def generate_phone_events(days: int, per_day: int) -> List[dict]:
    events = []
    for day in range(days):
        base_hours = 24 * day + random.randint(1, 3)
        for _ in range(per_day):
            number, name, direction = random.choice(PHONE_CONTACTS)
            duration = random.randint(5, 20)
            events.append({
                "timestamp_start": -(base_hours + random.randint(0, 5)),
                "duration": duration,
                "phone_number": number,
                "contact_name": name,
                "direction": direction,
            })
    return events


def main():
    parser = argparse.ArgumentParser(description="Seed dummy data into the API")
    parser.add_argument("--base-url", default="http://localhost:8000", help="FastAPI base URL")
    parser.add_argument("--user-id", default="demo", help="User ID to tag events with")
    parser.add_argument("--machine-id", default="demo-pc", help="Machine ID for window events")
    parser.add_argument("--device-id", default="demo-iphone", help="Device ID for phone events")
    parser.add_argument("--days", type=int, default=10, help="Number of days to generate")
    parser.add_argument("--windows-per-day", type=int, default=5, help="Window events per day")
    parser.add_argument("--calls-per-day", type=int, default=2, help="Phone calls per day")
    args = parser.parse_args()

    session = requests.Session()
    base = args.base_url.rstrip("/")

    print(f"Seeding projects on {base}")
    projects = ensure_projects(session, base)
    milestones = ensure_milestones(session, base, projects)

    window_events = generate_window_events(args.days, args.windows_per_day)
    phone_events = generate_phone_events(args.days, args.calls_per_day)

    print(f"Creating {len(window_events)} window events and {len(phone_events)} phone events…")
    event_ids = []
    for payload in window_events:
        event_ids.append(
            create_window_event(
                session,
                base,
                start_hours=payload["timestamp_start"],
                duration_minutes=payload["duration"],
                window_title=payload["window_title"],
                process_name=payload["process_name"],
                machine_id=args.machine_id,
                user_id=args.user_id,
            )
        )
    for payload in phone_events:
        event_ids.append(
            create_phone_event(
                session,
                base,
                start_hours=payload["timestamp_start"],
                duration_minutes=payload["duration"],
                number=payload["phone_number"],
                name=payload["contact_name"],
                direction=payload["direction"],
                device_id=args.device_id,
                user_id=args.user_id,
            )
        )

    print("Creating assignments…")
    for event_id in event_ids:
        project = random.choice(list(projects.values()))
        milestone_candidates = [m for m in milestones.values() if m["project_id"] == project["id"]]
        milestone = random.choice(milestone_candidates) if milestone_candidates else None
        payload = {
            "event_id": event_id,
            "project_id": project["id"],
            "milestone_id": milestone["id"] if milestone else None,
            "activity_type": random.choice(ACTIVITIES),
            "comment": "Demo-Eintrag",
        }
        session.post(f"{base}/assignments", json=payload, timeout=10)

    print("Done. Check the Web-UI for demo rows across multiple days.")


def ensure_projects(session: requests.Session, base: str) -> Dict[str, Dict]:
    existing = session.get(f"{base}/projects", timeout=10).json()
    proj_map = {p["name"]: p for p in existing}
    for project in PROJECTS:
        if project["name"] in proj_map:
            continue
        res = session.post(f"{base}/projects", json=project, timeout=10)
        res.raise_for_status()
        proj_map[project["name"]] = res.json()
    return proj_map


def ensure_milestones(session: requests.Session, base: str, projects: Dict[str, Dict]) -> Dict[str, Dict]:
    existing = session.get(f"{base}/milestones", timeout=10).json()
    milestone_map = {f'{m["project_id"]}:{m["name"]}': m for m in existing}
    for milestone in MILESTONES:
        key = f'{projects[milestone["project"]]["id"]}:{milestone["name"]}'
        if key in milestone_map:
            continue
        payload = {
            "project_id": projects[milestone["project"]]["id"],
            "name": milestone["name"],
            "soll_stunden": milestone["soll_stunden"],
            "bonus_relevant": milestone["bonus_relevant"],
            "ist_stunden": milestone["ist_stunden"],
        }
        res = session.post(f"{base}/milestones", json=payload, timeout=10)
        res.raise_for_status()
        milestone_map[key] = res.json()
    return milestone_map


def create_window_event(session, base, start_hours, duration_minutes, window_title, process_name, machine_id, user_id):
    start = iso(abs(start_hours))
    end = start + dt.timedelta(minutes=duration_minutes)
    payload = {
        "timestamp_start": start.isoformat() + "Z",
        "timestamp_end": end.isoformat() + "Z",
        "window_title": window_title,
        "process_name": process_name,
        "duration_seconds": int(duration_minutes * 60),
        "machine_id": machine_id,
        "user_id": user_id,
    }
    res = session.post(f"{base}/events/window", json=payload, timeout=10)
    res.raise_for_status()
    return res.json()["id"]


def create_phone_event(session, base, start_hours, duration_minutes, number, name, direction, device_id, user_id):
    start = iso(abs(start_hours))
    end = start + dt.timedelta(minutes=duration_minutes)
    payload = {
        "timestamp_start": start.isoformat() + "Z",
        "timestamp_end": end.isoformat() + "Z",
        "phone_number": number,
        "contact_name": name,
        "direction": direction,
        "duration_seconds": int(duration_minutes * 60),
        "device_id": device_id,
        "user_id": user_id,
    }
    res = session.post(f"{base}/events/phone", json=payload, timeout=10)
    res.raise_for_status()
    return res.json()["id"]


if __name__ == "__main__":
    main()

