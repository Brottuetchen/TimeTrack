"""
PyQt6 System Tray Controller für TimeTrack Windows Agent
"""
import logging
from typing import Optional

from PyQt6.QtCore import QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QMessageBox


class TrayController(QObject):
    """
    PyQt6-basierter System Tray Controller.

    Signals:
        dashboard_requested: Dashboard-Fenster soll geöffnet werden
        quick_assign_requested: Quick-Assign-Dialog soll geöffnet werden
        settings_requested: Settings-Dialog soll geöffnet werden
        tracking_toggled: Tracking ein/aus geschaltet (bool)
        send_now_requested: Manuelle Event-Übertragung
        call_sync_requested: Manueller Call-Sync
        quit_requested: Anwendung beenden
    """

    dashboard_requested = pyqtSignal()
    quick_assign_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    tracking_toggled = pyqtSignal(bool)
    send_now_requested = pyqtSignal()
    call_sync_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(
        self,
        app: QApplication,
        logger: logging.Logger,
        tracking_enabled: bool = True,
        call_sync_enabled: bool = False
    ):
        super().__init__()
        self.app = app
        self.logger = logger
        self.tracking_enabled = tracking_enabled
        self.call_sync_enabled = call_sync_enabled

        # System Tray Icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self._create_icon(active=tracking_enabled))
        self.tray_icon.setToolTip("TimeTrack - aktiv" if tracking_enabled else "TimeTrack - pausiert")

        # Menü erstellen
        self._create_menu()

        # Double-Click öffnet Dashboard
        self.tray_icon.activated.connect(self._on_tray_activated)

        # Auto-Update Timer für Tooltip
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_tooltip)
        self.update_timer.start(15000)  # Alle 15 Sekunden

        # Status-Daten
        self.buffer_count = 0
        self.last_upload = "noch nie"
        self.last_error = "–"
        self.privacy_label = "aktiv"
        self.call_sync_status = None

        self.tray_icon.show()
        self.logger.info("PyQt6 System Tray initialisiert")

    def _create_icon(self, active: bool) -> QIcon:
        """Erstellt ein farbiges Icon (grün=aktiv, orange=pausiert)."""
        pixmap = QPixmap(64, 64)
        color = QColor(0, 180, 0) if active else QColor(200, 80, 0)
        pixmap.fill(color)

        painter = QPainter(pixmap)
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(16, 16, 32, 32)
        painter.end()

        return QIcon(pixmap)

    def _create_menu(self):
        """Erstellt das Kontextmenü."""
        menu = QMenu()

        # Dashboard
        dashboard_action = QAction("Dashboard öffnen", self)
        dashboard_action.triggered.connect(lambda: self.dashboard_requested.emit())
        menu.addAction(dashboard_action)

        # Quick-Assign
        quick_assign_action = QAction("Quick-Assign", self)
        quick_assign_action.triggered.connect(lambda: self.quick_assign_requested.emit())
        menu.addAction(quick_assign_action)

        menu.addSeparator()

        # Tracking Toggle
        self.tracking_action = QAction("Tracking aktiv", self)
        self.tracking_action.setCheckable(True)
        self.tracking_action.setChecked(self.tracking_enabled)
        self.tracking_action.triggered.connect(self._toggle_tracking)
        menu.addAction(self.tracking_action)

        # Send Now
        send_action = QAction("Events jetzt senden", self)
        send_action.triggered.connect(lambda: self.send_now_requested.emit())
        menu.addAction(send_action)

        menu.addSeparator()

        # Call-Sync (nur wenn aktiviert)
        if self.call_sync_enabled:
            call_sync_action = QAction("Call-Sync jetzt", self)
            call_sync_action.triggered.connect(lambda: self.call_sync_requested.emit())
            menu.addAction(call_sync_action)
            menu.addSeparator()

        # Settings
        settings_action = QAction("Einstellungen", self)
        settings_action.triggered.connect(lambda: self.settings_requested.emit())
        menu.addAction(settings_action)

        # Status
        status_action = QAction("Status anzeigen", self)
        status_action.triggered.connect(self.show_status)
        menu.addAction(status_action)

        menu.addSeparator()

        # Beenden
        quit_action = QAction("Beenden", self)
        quit_action.triggered.connect(lambda: self.quit_requested.emit())
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)

    def _on_tray_activated(self, reason):
        """Handle Tray-Icon Klicks."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.dashboard_requested.emit()

    def _toggle_tracking(self, checked: bool):
        """Tracking ein/aus schalten."""
        self.tracking_enabled = checked
        self.tray_icon.setIcon(self._create_icon(active=checked))
        self.tracking_toggled.emit(checked)
        self.update_tooltip()
        self.logger.info(f"Tracking {'aktiviert' if checked else 'pausiert'}")

    def show_status(self):
        """Zeigt Status-Dialog."""
        status_text = self._build_status_text()
        QMessageBox.information(None, "TimeTrack Status", status_text)

    def _build_status_text(self) -> str:
        """Baut Status-Text."""
        lines = [
            f"Tracking: {'aktiv' if self.tracking_enabled else 'pausiert'}",
            f"Offene Events: {self.buffer_count}",
            f"Letzter Upload: {self.last_upload}",
            f"Letzter Fehler: {self.last_error}",
            f"Privacy-Modus: {self.privacy_label}"
        ]

        if self.call_sync_enabled and self.call_sync_status:
            sync_ok = "✓" if self.call_sync_status.get("last_sync_success") else "✗"
            last_sync = self.call_sync_status.get("last_sync_time", "noch nie")
            if last_sync != "noch nie":
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(last_sync)
                    last_sync = dt.strftime("%d.%m.%Y %H:%M")
                except:
                    pass

            next_sync_min = int(self.call_sync_status.get("next_sync_in_seconds", 0) / 60)

            lines.extend([
                "",
                f"Call-Sync: {sync_ok} (alle {self.call_sync_status['interval_minutes']} min)",
                f"Letzter Sync: {last_sync}",
                f"Nächster Sync in: {next_sync_min} min"
            ])

            if error := self.call_sync_status.get("last_sync_error"):
                lines.append(f"Fehler: {error[:50]}")

        return "\n".join(lines)

    def update_status(
        self,
        buffer_count: int = 0,
        last_upload: str = "noch nie",
        last_error: str = "–",
        privacy_label: str = "aktiv",
        call_sync_status: Optional[dict] = None
    ):
        """Update Status-Daten."""
        self.buffer_count = buffer_count
        self.last_upload = last_upload
        self.last_error = last_error
        self.privacy_label = privacy_label
        self.call_sync_status = call_sync_status

    def update_tooltip(self):
        """Update Tooltip."""
        status = "aktiv" if self.tracking_enabled else "pausiert"
        tooltip = f"TimeTrack – {status}"
        if self.buffer_count > 0:
            tooltip += f" ({self.buffer_count} Events)"
        self.tray_icon.setToolTip(tooltip)

    def show_notification(self, title: str, message: str):
        """Zeigt System-Notification."""
        self.tray_icon.showMessage(
            title,
            message,
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )

    def cleanup(self):
        """Cleanup vor Beenden."""
        self.update_timer.stop()
        self.tray_icon.hide()
        self.logger.info("PyQt6 Tray Controller beendet")
