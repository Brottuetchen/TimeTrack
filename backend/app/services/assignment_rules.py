"""
Assignment Rules Engine - 100% lokal, kein ML-Cloud-Service.
Verwendet einfache Regex/String-Matching.
"""

import re
from typing import Optional
from sqlalchemy.orm import Session as DBSession

from ..models import Event, Session as SessionModel, AssignmentRule, Assignment


class RulesEngine:
    def __init__(self, db: DBSession):
        self.db = db

    def apply_rules_to_event(self, event: Event) -> Optional[Assignment]:
        """
        Wendet Regeln auf Event an (lokal evaluiert).
        Returniert Assignment wenn Regel matcht, sonst None.
        """
        rules = self.db.query(AssignmentRule).filter(
            AssignmentRule.user_id == event.user_id,
            AssignmentRule.enabled == True,
        ).order_by(AssignmentRule.priority.desc()).all()

        for rule in rules:
            if self._matches_rule(event, rule):
                return self._create_assignment_from_rule(event, rule)

        return None

    def apply_rules_to_session(self, session: SessionModel) -> Optional[Assignment]:
        """
        Wendet Regeln auf Session an (lokal evaluiert).
        Returniert Assignment wenn Regel matcht, sonst None.
        """
        rules = self.db.query(AssignmentRule).filter(
            AssignmentRule.user_id == session.user_id,
            AssignmentRule.enabled == True,
        ).order_by(AssignmentRule.priority.desc()).all()

        for rule in rules:
            if self._matches_rule_session(session, rule):
                return self._create_assignment_from_rule_session(session, rule)

        return None

    def _matches_rule(self, event: Event, rule: AssignmentRule) -> bool:
        """Prüft ob Event die Regel erfüllt (lokal, kein API-Call)"""

        # Prozess-Pattern
        if rule.process_pattern:
            if not self._matches_pattern(event.process_name, rule.process_pattern):
                return False

        # Titel-Contains
        if rule.title_contains and event.window_title:
            if rule.title_contains.lower() not in event.window_title.lower():
                return False

        # Titel-Regex (für komplexere Matches)
        if rule.title_regex and event.window_title:
            try:
                if not re.search(rule.title_regex, event.window_title, re.IGNORECASE):
                    return False
            except re.error:
                # Ungültige Regex → ignorieren
                pass

        return True

    def _matches_rule_session(self, session: SessionModel, rule: AssignmentRule) -> bool:
        """Prüft ob Session die Regel erfüllt (lokal, kein API-Call)"""

        # Prozess-Pattern
        if rule.process_pattern:
            if not self._matches_pattern(session.process_name, rule.process_pattern):
                return False

        # Titel-Contains
        if rule.title_contains and session.window_title_base:
            if rule.title_contains.lower() not in session.window_title_base.lower():
                return False

        # Titel-Regex (für komplexere Matches)
        if rule.title_regex and session.window_title_base:
            try:
                if not re.search(rule.title_regex, session.window_title_base, re.IGNORECASE):
                    return False
            except re.error:
                # Ungültige Regex → ignorieren
                pass

        return True

    def _matches_pattern(self, value: str, pattern: str) -> bool:
        """Simples Wildcard-Matching (* und ?)"""
        regex_pattern = pattern.replace('.', '\\.').replace('*', '.*').replace('?', '.')
        return bool(re.match(f"^{regex_pattern}$", value, re.IGNORECASE))

    def _create_assignment_from_rule(self, event: Event, rule: AssignmentRule) -> Assignment:
        """Erstellt Assignment basierend auf Regel"""
        comment = rule.auto_comment_template or f"Auto-assigned via rule: {rule.name}"

        # Template-Variablen ersetzen
        if event.window_title:
            comment = comment.replace("{title}", event.window_title)
        comment = comment.replace("{process}", event.process_name)

        assignment = Assignment(
            event_id=event.id,
            project_id=rule.auto_project_id,
            milestone_id=rule.auto_milestone_id,
            activity_type=rule.auto_activity,
            comment=comment,
        )

        self.db.add(assignment)
        return assignment

    def _create_assignment_from_rule_session(self, session: SessionModel, rule: AssignmentRule) -> Assignment:
        """Erstellt Assignment basierend auf Regel für Session"""
        comment = rule.auto_comment_template or f"Auto-assigned via rule: {rule.name}"

        # Template-Variablen ersetzen
        if session.window_title_base:
            comment = comment.replace("{title}", session.window_title_base)
        comment = comment.replace("{process}", session.process_name)

        assignment = Assignment(
            event_id=session.event_ids[0] if session.event_ids else None,  # Dummy event_id
            project_id=rule.auto_project_id,
            milestone_id=rule.auto_milestone_id,
            activity_type=rule.auto_activity,
            comment=comment,
        )

        self.db.add(assignment)
        return assignment


def auto_apply_rules_to_event(event: Event, db: DBSession):
    """Wird nach Event-Creation aufgerufen"""
    engine = RulesEngine(db)
    assignment = engine.apply_rules_to_event(event)
    if assignment:
        db.commit()
    return assignment


def auto_apply_rules_to_session(session: SessionModel, db: DBSession):
    """Wird nach Session-Creation aufgerufen"""
    engine = RulesEngine(db)
    assignment = engine.apply_rules_to_session(session)
    if assignment:
        session.assignment_id = assignment.id
        db.commit()
    return assignment
