"""
Session Aggregation Service - 100% lokal, keine externen APIs.

Algorithmus:
1. Sortiere Events nach timestamp_start
2. Gruppiere Events mit gleichem Prozess + ähnlichem Titel
3. Merge Events wenn Pause <5 Minuten
4. Erstelle Session-Objekte
"""

from datetime import datetime, timedelta
from typing import List, Optional
from difflib import SequenceMatcher
import re

from sqlalchemy.orm import Session as DBSession
from ..models import Event, Session as SessionModel


class SessionAggregator:
    def __init__(
        self,
        max_break_minutes: int = 5,
        min_title_similarity: float = 0.65,
        min_session_duration_seconds: int = 120,
    ):
        self.max_break_minutes = max_break_minutes
        self.min_title_similarity = min_title_similarity
        self.min_session_duration_seconds = min_session_duration_seconds

    def aggregate_events(
        self,
        events: List[Event],
        user_id: str,
    ) -> List[SessionModel]:
        """
        Aggregiert Events zu Sessions. Komplett lokal, kein Network I/O.
        """
        if not events:
            return []

        # Sortiere nach Startzeit
        sorted_events = sorted(events, key=lambda e: e.timestamp_start)

        sessions = []
        current_session = None

        for event in sorted_events:
            # Ignoriere Events ohne Ende-Zeit oder zu kurz
            if not event.timestamp_end or event.duration_seconds < 10:
                continue

            if not current_session:
                # Erste Session starten
                current_session = self._create_session_from_event(event, user_id)
                continue

            # Prüfe ob Event zur aktuellen Session gehört
            if self._belongs_to_session(event, current_session):
                self._merge_event_into_session(event, current_session)
            else:
                # Session abschließen (wenn lang genug)
                if current_session['total_duration'] >= self.min_session_duration_seconds:
                    sessions.append(self._finalize_session(current_session))

                # Neue Session starten
                current_session = self._create_session_from_event(event, user_id)

        # Letzte Session abschließen
        if current_session and current_session['total_duration'] >= self.min_session_duration_seconds:
            sessions.append(self._finalize_session(current_session))

        return sessions

    def _create_session_from_event(self, event: Event, user_id: str) -> dict:
        """Erstellt neue Session aus erstem Event"""
        return {
            'user_id': user_id,
            'process_name': event.process_name,
            'window_title_base': self._normalize_title(event.window_title),
            'start_time': event.timestamp_start,
            'end_time': event.timestamp_end,
            'total_duration_seconds': event.duration_seconds,
            'active_duration_seconds': event.duration_seconds,
            'event_ids': [event.id],
            'event_count': 1,
            'break_count': 0,
            'is_private': event.is_private,
        }

    def _belongs_to_session(self, event: Event, session: dict) -> bool:
        """
        Prüft ob Event zur Session gehört (lokal, keine API-Calls).

        Bedingungen:
        1. Gleicher Prozess
        2. Ähnlicher Titel (Fuzzy-Match)
        3. Pause <5 Minuten seit letztem Event
        """
        # 1. Prozess-Check
        if event.process_name != session['process_name']:
            return False

        # 2. Titel-Ähnlichkeit (lokal berechnet)
        if event.window_title and session['window_title_base']:
            normalized_title = self._normalize_title(event.window_title)
            similarity = self._title_similarity(
                normalized_title,
                session['window_title_base']
            )
            if similarity < self.min_title_similarity:
                return False

        # 3. Zeit-Lücke
        time_gap = (event.timestamp_start - session['end_time']).total_seconds() / 60
        if time_gap > self.max_break_minutes:
            return False

        return True

    def _merge_event_into_session(self, event: Event, session: dict):
        """Fügt Event zu bestehender Session hinzu"""
        # Berechne Pause
        gap_seconds = (event.timestamp_start - session['end_time']).total_seconds()

        # Update Session
        session['end_time'] = event.timestamp_end
        session['event_ids'].append(event.id)
        session['event_count'] += 1
        session['active_duration_seconds'] += event.duration_seconds
        session['total_duration_seconds'] = int((session['end_time'] - session['start_time']).total_seconds())

        if gap_seconds > 60:  # Pause >1 Minute zählt als Break
            session['break_count'] += 1

    def _finalize_session(self, session: dict) -> SessionModel:
        """Konvertiert dict zu SQLAlchemy-Model"""
        return SessionModel(**session)

    def _normalize_title(self, title: Optional[str]) -> str:
        """
        Normalisiert Fenstertitel für besseres Matching (lokal).

        Beispiele:
        - "Projekt-X.dwg - AutoCAD 2024" → "projekt-x.dwg"
        - "Document1 (v2) - Word" → "document1"
        """
        if not title:
            return ""

        title = title.lower()

        # Entferne Programmnamen am Ende
        title = re.sub(r'\s*-\s*(autocad|word|excel|chrome|firefox|code|visual studio).*$', '', title)

        # Entferne Versionsnummern
        title = re.sub(r'\s*\(v?\d+\)\s*', ' ', title)
        title = re.sub(r'\s*-\s*\d{4}$', '', title)  # Jahr am Ende

        # Entferne mehrfache Leerzeichen
        title = ' '.join(title.split())

        return title.strip()

    def _title_similarity(self, title1: str, title2: str) -> float:
        """
        Berechnet Titel-Ähnlichkeit lokal (Python difflib).
        Keine externen APIs!
        """
        return SequenceMatcher(None, title1, title2).ratio()


def aggregate_user_events(
    db: DBSession,
    user_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[SessionModel]:
    """
    High-Level Funktion: Aggregiert Events eines Users zu Sessions.
    Speichert Sessions in DB.
    """
    # Events laden
    query = db.query(Event).filter(
        Event.user_id == user_id,
        Event.source_type == 'window',  # Nur Fenster-Events
    )

    if start_date:
        query = query.filter(Event.timestamp_start >= start_date)
    if end_date:
        query = query.filter(Event.timestamp_start <= end_date)

    events = query.order_by(Event.timestamp_start).all()

    # Aggregiere lokal
    aggregator = SessionAggregator()
    sessions = aggregator.aggregate_events(events, user_id)

    # Speichere Sessions
    for session in sessions:
        db.add(session)

    db.commit()

    return sessions
