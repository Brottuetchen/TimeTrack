"""
Quick-Assign Dialog für schnelles Zuweisen von Events
"""
import logging
from typing import Optional, List, Dict

import requests
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QGroupBox,
)


class QuickAssignDialog(QDialog):
    """
    Quick-Assign Dialog zum schnellen Zuweisen von Events.

    Features:
    - Zeigt letzte 20 unzugewiesene Events
    - Multi-Select für Bulk-Assign
    - Projekt + Milestone Auswahl
    - Aktivitätstyp
    - Kommentar
    """

    def __init__(
        self,
        logger: logging.Logger,
        base_url: str,
        user_id: str,
        api_key: Optional[str] = None,
        verify_ssl: bool = False,
        parent=None
    ):
        super().__init__(parent)
        self.logger = logger
        self.base_url = base_url.rstrip("/")
        self.user_id = user_id
        self.verify_ssl = verify_ssl

        self.session = requests.Session()
        if api_key:
            self.session.headers["Authorization"] = f"Bearer {api_key}"

        self.projects = []
        self.milestones = []
        self.selected_events = []

        self.setWindowTitle("Quick-Assign")
        self.setModal(True)
        self.setGeometry(100, 100, 900, 600)

        # Dark Mode
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QComboBox, QLineEdit, QTextEdit {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #3a3a3a;
                padding: 6px;
                border-radius: 4px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #e0e0e0;
            }
            QPushButton {
                background-color: #0d7377;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #14a085;
            }
            QPushButton:disabled {
                background-color: #3a3a3a;
                color: #6a6a6a;
            }
            QTableWidget {
                background-color: #2d2d2d;
                color: #e0e0e0;
                gridline-color: #3a3a3a;
                border: 1px solid #3a3a3a;
            }
            QHeaderView::section {
                background-color: #3a3a3a;
                color: #e0e0e0;
                padding: 6px;
                border: 1px solid #4a4a4a;
            }
            QGroupBox {
                color: #e0e0e0;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                color: #0d7377;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        layout = QVBoxLayout(self)

        # Event-Auswahl
        events_box = self._create_events_box()
        layout.addWidget(events_box)

        # Assignment-Form
        form_box = self._create_form_box()
        layout.addWidget(form_box)

        # Buttons
        buttons = self._create_buttons()
        layout.addWidget(buttons)

        # Daten laden
        self._fetch_projects()
        self._fetch_events()

        self.logger.info("QuickAssignDialog geöffnet")

    def _create_events_box(self) -> QGroupBox:
        """Erstellt Event-Auswahl Box."""
        box = QGroupBox("Unzugewiesene Events (Mehrfachauswahl möglich)")
        layout = QVBoxLayout(box)

        self.events_table = QTableWidget()
        self.events_table.setColumnCount(4)
        self.events_table.setHorizontalHeaderLabels([
            "Zeit", "Typ", "Prozess/Kontakt", "Titel/Nummer"
        ])
        self.events_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.events_table.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)

        header = self.events_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.events_table)

        return box

    def _create_form_box(self) -> QGroupBox:
        """Erstellt Assignment-Form."""
        box = QGroupBox("Zuweisung")
        layout = QVBoxLayout(box)

        # Projekt
        proj_layout = QHBoxLayout()
        proj_layout.addWidget(QLabel("Projekt:"))
        self.project_combo = QComboBox()
        self.project_combo.currentIndexChanged.connect(self._on_project_changed)
        proj_layout.addWidget(self.project_combo, 1)
        layout.addLayout(proj_layout)

        # Milestone
        mile_layout = QHBoxLayout()
        mile_layout.addWidget(QLabel("Milestone:"))
        self.milestone_combo = QComboBox()
        mile_layout.addWidget(self.milestone_combo, 1)
        layout.addLayout(mile_layout)

        # Aktivitätstyp
        act_layout = QHBoxLayout()
        act_layout.addWidget(QLabel("Aktivität:"))
        self.activity_combo = QComboBox()
        self.activity_combo.addItems([
            "Planung", "Baustelle", "Dokumentation", "Meeting", "Fahrt", "Telefon", "PC"
        ])
        act_layout.addWidget(self.activity_combo, 1)
        layout.addLayout(act_layout)

        # Kommentar
        layout.addWidget(QLabel("Kommentar:"))
        self.comment_edit = QTextEdit()
        self.comment_edit.setMaximumHeight(80)
        layout.addWidget(self.comment_edit)

        return box

    def _create_buttons(self) -> QWidget:
        """Erstellt Button-Leiste."""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        layout.addStretch()

        # Abbrechen
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        # Zuweisen
        self.assign_btn = QPushButton("Zuweisen")
        self.assign_btn.clicked.connect(self._assign_events)
        layout.addWidget(self.assign_btn)

        return widget

    def _fetch_projects(self):
        """Lädt Projekte vom Backend."""
        try:
            url = f"{self.base_url}/projects"
            resp = self.session.get(url, verify=self.verify_ssl, timeout=5)

            if resp.status_code == 200:
                self.projects = resp.json()
                self.project_combo.clear()
                for proj in self.projects:
                    self.project_combo.addItem(
                        f"{proj['number']} - {proj['name']}",
                        proj['id']
                    )
                if self.projects:
                    self._on_project_changed(0)
            else:
                self.logger.warning(f"Projekte laden fehlgeschlagen: {resp.status_code}")

        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Projekte: {e}")

    def _on_project_changed(self, index: int):
        """Wenn Projekt geändert wird, lade Milestones."""
        if index < 0 or not self.projects:
            return

        project_id = self.project_combo.currentData()
        self._fetch_milestones(project_id)

    def _fetch_milestones(self, project_id: int):
        """Lädt Milestones für Projekt."""
        try:
            url = f"{self.base_url}/milestones"
            params = {"project_id": project_id}
            resp = self.session.get(url, params=params, verify=self.verify_ssl, timeout=5)

            if resp.status_code == 200:
                self.milestones = resp.json()
                self.milestone_combo.clear()
                for mile in self.milestones:
                    self.milestone_combo.addItem(
                        f"{mile['number']} - {mile['name']}",
                        mile['id']
                    )
            else:
                self.logger.warning(f"Milestones laden fehlgeschlagen: {resp.status_code}")

        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Milestones: {e}")

    def _fetch_events(self):
        """Lädt unzugewiesene Events."""
        try:
            url = f"{self.base_url}/events/unassigned"
            params = {
                "user_id": self.user_id,
                "limit": 20
            }
            resp = self.session.get(url, params=params, verify=self.verify_ssl, timeout=5)

            if resp.status_code == 200:
                events = resp.json()
                self._populate_events_table(events)
            else:
                self.logger.warning(f"Events laden fehlgeschlagen: {resp.status_code}")

        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Events: {e}")

    def _populate_events_table(self, events: List[Dict]):
        """Füllt Event-Tabelle."""
        self.selected_events = events
        self.events_table.setRowCount(len(events))

        for row, event in enumerate(events):
            from datetime import datetime

            # Zeit
            timestamp = event.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                time_str = dt.strftime("%H:%M")
            except:
                time_str = timestamp[:5] if timestamp else "–"

            # Typ
            source_type = event.get("source_type", "window")

            # Prozess/Kontakt
            proc = event.get("process_name") or event.get("contact_name") or "–"

            # Titel/Nummer
            title = event.get("window_title") or event.get("phone_number") or "–"

            self.events_table.setItem(row, 0, QTableWidgetItem(time_str))
            self.events_table.setItem(row, 1, QTableWidgetItem(source_type))
            self.events_table.setItem(row, 2, QTableWidgetItem(proc))
            self.events_table.setItem(row, 3, QTableWidgetItem(title))

            # Event-ID als UserRole speichern
            item = self.events_table.item(row, 0)
            item.setData(Qt.ItemDataRole.UserRole, event['id'])

    def _assign_events(self):
        """Weist ausgewählte Events zu."""
        selected_rows = set(item.row() for item in self.events_table.selectedItems())

        if not selected_rows:
            QMessageBox.warning(self, "Fehler", "Bitte mindestens ein Event auswählen")
            return

        project_id = self.project_combo.currentData()
        milestone_id = self.milestone_combo.currentData()
        activity = self.activity_combo.currentText()
        comment = self.comment_edit.toPlainText().strip()

        if not project_id:
            QMessageBox.warning(self, "Fehler", "Bitte ein Projekt auswählen")
            return

        # Event-IDs sammeln
        event_ids = []
        for row in selected_rows:
            item = self.events_table.item(row, 0)
            event_id = item.data(Qt.ItemDataRole.UserRole)
            event_ids.append(event_id)

        # Bulk-Assignment erstellen
        try:
            url = f"{self.base_url}/assignments/bulk"
            payload = {
                "event_ids": event_ids,
                "project_id": project_id,
                "milestone_id": milestone_id,
                "activity_type": activity,
                "comment": comment
            }

            resp = self.session.post(url, json=payload, verify=self.verify_ssl, timeout=10)

            if resp.status_code == 200:
                result = resp.json()
                QMessageBox.information(
                    self,
                    "Erfolg",
                    f"{result.get('assigned_count', len(event_ids))} Event(s) zugewiesen"
                )
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    "Fehler",
                    f"Zuweisung fehlgeschlagen: {resp.status_code}\n{resp.text}"
                )

        except Exception as e:
            self.logger.exception(f"Fehler bei Zuweisung: {e}")
            QMessageBox.critical(self, "Fehler", f"Fehler bei Zuweisung:\n{str(e)}")
