"""
Dashboard Widget mit Live-Event-Preview und Statistiken
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict

import requests
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
)


class DashboardWidget(QWidget):
    """
    Dashboard mit:
    - Live-Event-Preview (letzte 10 Events)
    - Tagesstatistiken (Events heute, Upload-Status)
    - Privacy-Mode-Toggle
    - Refresh-Button
    """

    privacy_toggle_requested = pyqtSignal(bool)
    refresh_requested = pyqtSignal()

    def __init__(
        self,
        logger: logging.Logger,
        base_url: str,
        user_id: str,
        api_key: Optional[str] = None,
        verify_ssl: bool = False
    ):
        super().__init__()
        self.logger = logger
        self.base_url = base_url.rstrip("/")
        self.user_id = user_id
        self.verify_ssl = verify_ssl

        self.session = requests.Session()
        if api_key:
            self.session.headers["Authorization"] = f"Bearer {api_key}"

        layout = QVBoxLayout(self)

        # Statistiken Box
        stats_box = self._create_stats_box()
        layout.addWidget(stats_box)

        # Actions
        actions = self._create_actions()
        layout.addWidget(actions)

        # Event-Tabelle
        events_box = self._create_events_table()
        layout.addWidget(events_box)

        # Auto-Refresh Timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._fetch_events)
        self.refresh_timer.start(10000)  # Alle 10 Sekunden

        # Initial Load
        self._fetch_events()

        self.logger.info("DashboardWidget initialisiert")

    def _create_stats_box(self) -> QGroupBox:
        """Erstellt Statistik-Box."""
        box = QGroupBox("Heute")
        layout = QHBoxLayout(box)

        self.stats_events_label = QLabel("Events: 0")
        self.stats_events_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.stats_events_label)

        layout.addStretch()

        self.stats_upload_label = QLabel("Offene Events: 0")
        self.stats_upload_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.stats_upload_label)

        layout.addStretch()

        self.stats_privacy_label = QLabel("Privacy: aktiv")
        self.stats_privacy_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.stats_privacy_label)

        return box

    def _create_actions(self) -> QWidget:
        """Erstellt Action-Buttons."""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Refresh Button
        refresh_btn = QPushButton("Aktualisieren")
        refresh_btn.clicked.connect(self._fetch_events)
        layout.addWidget(refresh_btn)

        layout.addStretch()

        # Privacy-Mode Toggle (wird später aktiviert)
        self.privacy_btn = QPushButton("Privacy-Mode aktivieren")
        self.privacy_btn.setEnabled(False)  # Disabled - Backend-Integration nötig
        layout.addWidget(self.privacy_btn)

        return widget

    def _create_events_table(self) -> QGroupBox:
        """Erstellt Event-Tabelle."""
        box = QGroupBox("Letzte Events")
        layout = QVBoxLayout(box)

        self.events_table = QTableWidget()
        self.events_table.setColumnCount(5)
        self.events_table.setHorizontalHeaderLabels([
            "Zeit", "Typ", "Prozess", "Titel", "Dauer"
        ])

        # Column Widths
        header = self.events_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.events_table)

        return box

    def _fetch_events(self):
        """Lädt Events vom Backend."""
        try:
            url = f"{self.base_url}/events"
            params = {
                "user_id": self.user_id,
                "limit": 10,
                "offset": 0
            }

            resp = self.session.get(url, params=params, verify=self.verify_ssl, timeout=5)

            if resp.status_code == 200:
                events = resp.json()
                self.update_events(events)
            else:
                self.logger.warning(f"Events laden fehlgeschlagen: {resp.status_code}")

        except requests.RequestException as e:
            self.logger.error(f"Fehler beim Laden der Events: {e}")
        except Exception as e:
            self.logger.exception(f"Unerwarteter Fehler: {e}")

    def update_events(self, events: List[Dict]):
        """Update Event-Tabelle."""
        self.events_table.setRowCount(len(events))

        for row, event in enumerate(events):
            # Zeit
            timestamp = event.get("timestamp")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    time_str = dt.strftime("%H:%M:%S")
                except:
                    time_str = timestamp[:8]
            else:
                time_str = "–"

            # Typ
            source_type = event.get("source_type", "window")

            # Prozess
            process_name = event.get("process_name") or event.get("contact_name") or "–"

            # Titel
            window_title = event.get("window_title") or event.get("phone_number") or "–"

            # Dauer
            duration = event.get("duration_seconds", 0)
            duration_str = self._format_duration(duration)

            # Setze Items
            self.events_table.setItem(row, 0, QTableWidgetItem(time_str))
            self.events_table.setItem(row, 1, QTableWidgetItem(source_type))
            self.events_table.setItem(row, 2, QTableWidgetItem(process_name))
            self.events_table.setItem(row, 3, QTableWidgetItem(window_title))
            self.events_table.setItem(row, 4, QTableWidgetItem(duration_str))

        # Update Statistiken
        self.stats_events_label.setText(f"Events: {len(events)}")

    def update_stats(self, buffer_count: int, privacy_label: str):
        """Update Statistiken."""
        self.stats_upload_label.setText(f"Offene Events: {buffer_count}")
        self.stats_privacy_label.setText(f"Privacy: {privacy_label}")

    def _format_duration(self, seconds: int) -> str:
        """Formatiert Dauer."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m"
        else:
            hours = seconds // 3600
            mins = (seconds % 3600) // 60
            return f"{hours}h {mins}m"

    def cleanup(self):
        """Cleanup."""
        self.refresh_timer.stop()
        self.logger.info("DashboardWidget beendet")
