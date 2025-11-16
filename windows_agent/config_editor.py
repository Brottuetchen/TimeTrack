"""
Config Editor UI für TimeTrack Agent
Ermöglicht die Bearbeitung der Konfiguration über ein GUI
"""

import json
import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ConfigEditorDialog(QDialog):
    """Dialog zum Bearbeiten der Agent-Konfiguration"""

    config_saved = pyqtSignal()

    def __init__(self, config_path: Path, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config_path = config_path
        self.setWindowTitle("TimeTrack Agent - Konfiguration")
        self.setMinimumWidth(600)
        self.setMinimumHeight(700)

        self.init_ui()
        self.load_config()

    def init_ui(self):
        """Erstellt das UI"""
        layout = QVBoxLayout()

        # Info-Label
        info_label = QLabel(
            "Konfiguriere den TimeTrack Agent. Änderungen werden erst nach einem Neustart aktiv."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("background-color: #e3f2fd; padding: 10px; border-radius: 5px;")
        layout.addWidget(info_label)

        # Basis-Einstellungen
        layout.addWidget(self._create_basic_group())

        # Tracking-Einstellungen
        layout.addWidget(self._create_tracking_group())

        # Filter-Einstellungen
        layout.addWidget(self._create_filter_group())

        # Call-Sync Einstellungen
        layout.addWidget(self._create_callsync_group())

        # Buttons
        button_layout = QHBoxLayout()

        self.save_btn = QPushButton("Speichern")
        self.save_btn.clicked.connect(self.save_config)
        self.save_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")

        self.cancel_btn = QPushButton("Abbrechen")
        self.cancel_btn.clicked.connect(self.reject)

        self.reset_btn = QPushButton("Auf Standard zurücksetzen")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        self.reset_btn.setStyleSheet("background-color: #ff9800; color: white; padding: 8px;")

        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _create_basic_group(self) -> QGroupBox:
        """Erstellt die Basis-Einstellungen Gruppe"""
        group = QGroupBox("Basis-Einstellungen")
        form = QFormLayout()

        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("http://localhost:8000")
        form.addRow("Backend URL:", self.base_url_edit)

        self.user_id_edit = QLineEdit()
        self.user_id_edit.setPlaceholderText("deine_user_id")
        form.addRow("User ID:", self.user_id_edit)

        self.machine_id_edit = QLineEdit()
        self.machine_id_edit.setPlaceholderText("laptop-work")
        form.addRow("Machine ID:", self.machine_id_edit)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("Optional: API Key für Authentifizierung")
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("API Key:", self.api_key_edit)

        self.verify_ssl_check = QCheckBox("SSL-Zertifikate überprüfen")
        form.addRow("", self.verify_ssl_check)

        group.setLayout(form)
        return group

    def _create_tracking_group(self) -> QGroupBox:
        """Erstellt die Tracking-Einstellungen Gruppe"""
        group = QGroupBox("Tracking-Einstellungen")
        form = QFormLayout()

        self.poll_interval_spin = QSpinBox()
        self.poll_interval_spin.setRange(500, 10000)
        self.poll_interval_spin.setSuffix(" ms")
        self.poll_interval_spin.setValue(1500)
        form.addRow("Polling-Intervall:", self.poll_interval_spin)

        self.send_batch_spin = QSpinBox()
        self.send_batch_spin.setRange(10, 300)
        self.send_batch_spin.setSuffix(" Sekunden")
        self.send_batch_spin.setValue(30)
        form.addRow("Send-Intervall:", self.send_batch_spin)

        self.settings_poll_spin = QSpinBox()
        self.settings_poll_spin.setRange(15, 600)
        self.settings_poll_spin.setSuffix(" Sekunden")
        self.settings_poll_spin.setValue(60)
        form.addRow("Settings-Poll-Intervall:", self.settings_poll_spin)

        group.setLayout(form)
        return group

    def _create_filter_group(self) -> QGroupBox:
        """Erstellt die Filter-Einstellungen Gruppe"""
        group = QGroupBox("Filter-Einstellungen (lokal)")
        layout = QVBoxLayout()

        info = QLabel(
            "Hinweis: White/Blacklist können auch im Web-UI verwaltet werden.\n"
            "Diese lokalen Filter werden zusätzlich angewendet."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; font-size: 10px; padding: 5px;")
        layout.addWidget(info)

        form = QFormLayout()

        self.include_processes_edit = QTextEdit()
        self.include_processes_edit.setPlaceholderText("chrome.exe\nfirefox.exe\nvscode.exe\n(einer pro Zeile)")
        self.include_processes_edit.setMaximumHeight(80)
        form.addRow("Include Processes:", self.include_processes_edit)

        self.exclude_processes_edit = QTextEdit()
        self.exclude_processes_edit.setPlaceholderText("explorer.exe\nsystemsettings.exe\n(einer pro Zeile)")
        self.exclude_processes_edit.setMaximumHeight(80)
        form.addRow("Exclude Processes:", self.exclude_processes_edit)

        self.include_keywords_edit = QTextEdit()
        self.include_keywords_edit.setPlaceholderText("projekt\ncustomer\n(einer pro Zeile)")
        self.include_keywords_edit.setMaximumHeight(60)
        form.addRow("Include Title Keywords:", self.include_keywords_edit)

        self.exclude_keywords_edit = QTextEdit()
        self.exclude_keywords_edit.setPlaceholderText("private\npersonal\n(einer pro Zeile)")
        self.exclude_keywords_edit.setMaximumHeight(60)
        form.addRow("Exclude Title Keywords:", self.exclude_keywords_edit)

        layout.addLayout(form)
        group.setLayout(layout)
        return group

    def _create_callsync_group(self) -> QGroupBox:
        """Erstellt die Call-Sync Einstellungen Gruppe"""
        group = QGroupBox("Call-Sync Einstellungen")
        form = QFormLayout()

        self.callsync_enabled_check = QCheckBox("Call-Sync aktivieren")
        self.callsync_enabled_check.toggled.connect(self._toggle_callsync)
        form.addRow("", self.callsync_enabled_check)

        self.callsync_interval_spin = QSpinBox()
        self.callsync_interval_spin.setRange(5, 120)
        self.callsync_interval_spin.setSuffix(" Minuten")
        self.callsync_interval_spin.setValue(15)
        form.addRow("Sync-Intervall:", self.callsync_interval_spin)

        # Teams
        self.teams_enabled_check = QCheckBox("Microsoft Teams Sync")
        form.addRow("", self.teams_enabled_check)

        self.teams_tenant_edit = QLineEdit()
        self.teams_tenant_edit.setPlaceholderText("Tenant ID")
        form.addRow("Teams Tenant ID:", self.teams_tenant_edit)

        self.teams_client_edit = QLineEdit()
        self.teams_client_edit.setPlaceholderText("Client ID")
        form.addRow("Teams Client ID:", self.teams_client_edit)

        self.teams_secret_edit = QLineEdit()
        self.teams_secret_edit.setPlaceholderText("Client Secret")
        self.teams_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Teams Client Secret:", self.teams_secret_edit)

        # Placetel
        self.placetel_enabled_check = QCheckBox("Placetel Sync")
        form.addRow("", self.placetel_enabled_check)

        self.placetel_key_edit = QLineEdit()
        self.placetel_key_edit.setPlaceholderText("API Key")
        self.placetel_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Placetel API Key:", self.placetel_key_edit)

        self.placetel_url_edit = QLineEdit()
        self.placetel_url_edit.setPlaceholderText("https://api.placetel.de/v2")
        form.addRow("Placetel API URL:", self.placetel_url_edit)

        group.setLayout(form)
        return group

    def _toggle_callsync(self, enabled: bool):
        """Aktiviert/Deaktiviert Call-Sync Felder"""
        self.callsync_interval_spin.setEnabled(enabled)
        self.teams_enabled_check.setEnabled(enabled)
        self.teams_tenant_edit.setEnabled(enabled)
        self.teams_client_edit.setEnabled(enabled)
        self.teams_secret_edit.setEnabled(enabled)
        self.placetel_enabled_check.setEnabled(enabled)
        self.placetel_key_edit.setEnabled(enabled)
        self.placetel_url_edit.setEnabled(enabled)

    def load_config(self):
        """Lädt die Konfiguration aus der Datei"""
        if not self.config_path.exists():
            self.reset_to_defaults()
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Basis
            self.base_url_edit.setText(config.get('base_url', ''))
            self.user_id_edit.setText(config.get('user_id', ''))
            self.machine_id_edit.setText(config.get('machine_id', ''))
            self.api_key_edit.setText(config.get('api_key', ''))
            self.verify_ssl_check.setChecked(config.get('verify_ssl', False))

            # Tracking
            self.poll_interval_spin.setValue(config.get('poll_interval_ms', 1500))
            self.send_batch_spin.setValue(config.get('send_batch_seconds', 30))
            self.settings_poll_spin.setValue(config.get('settings_poll_seconds', 60))

            # Filter
            self.include_processes_edit.setPlainText('\n'.join(config.get('include_processes', [])))
            self.exclude_processes_edit.setPlainText('\n'.join(config.get('exclude_processes', [])))
            self.include_keywords_edit.setPlainText('\n'.join(config.get('include_title_keywords', [])))
            self.exclude_keywords_edit.setPlainText('\n'.join(config.get('exclude_title_keywords', [])))

            # Call-Sync
            self.callsync_enabled_check.setChecked(config.get('call_sync_enabled', False))
            self.callsync_interval_spin.setValue(config.get('call_sync_interval_minutes', 15))
            self.teams_enabled_check.setChecked(config.get('teams_enabled', False))
            self.teams_tenant_edit.setText(config.get('teams_tenant_id', '') or '')
            self.teams_client_edit.setText(config.get('teams_client_id', '') or '')
            self.teams_secret_edit.setText(config.get('teams_client_secret', '') or '')
            self.placetel_enabled_check.setChecked(config.get('placetel_enabled', False))
            self.placetel_key_edit.setText(config.get('placetel_api_key', '') or '')
            self.placetel_url_edit.setText(config.get('placetel_api_url', 'https://api.placetel.de/v2'))

        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Config konnte nicht geladen werden:\n{e}")
            self.reset_to_defaults()

    def save_config(self):
        """Speichert die Konfiguration"""
        # Validierung
        if not self.base_url_edit.text().strip():
            QMessageBox.warning(self, "Validierung", "Backend URL darf nicht leer sein!")
            return

        if not self.user_id_edit.text().strip():
            QMessageBox.warning(self, "Validierung", "User ID darf nicht leer sein!")
            return

        if not self.machine_id_edit.text().strip():
            QMessageBox.warning(self, "Validierung", "Machine ID darf nicht leer sein!")
            return

        try:
            # Config zusammenstellen
            config = {
                'base_url': self.base_url_edit.text().strip(),
                'user_id': self.user_id_edit.text().strip(),
                'machine_id': self.machine_id_edit.text().strip(),
                'api_key': self.api_key_edit.text().strip() or None,
                'verify_ssl': self.verify_ssl_check.isChecked(),
                'poll_interval_ms': self.poll_interval_spin.value(),
                'send_batch_seconds': self.send_batch_spin.value(),
                'settings_poll_seconds': self.settings_poll_spin.value(),
                'include_processes': [p.strip() for p in self.include_processes_edit.toPlainText().split('\n') if p.strip()],
                'exclude_processes': [p.strip() for p in self.exclude_processes_edit.toPlainText().split('\n') if p.strip()],
                'include_title_keywords': [k.strip() for k in self.include_keywords_edit.toPlainText().split('\n') if k.strip()],
                'exclude_title_keywords': [k.strip() for k in self.exclude_keywords_edit.toPlainText().split('\n') if k.strip()],
                'buffer_file': '%APPDATA%\\TimeTrack\\buffer.json',
                'log_file': '%APPDATA%\\TimeTrack\\agent.log',
                'call_sync_enabled': self.callsync_enabled_check.isChecked(),
                'call_sync_interval_minutes': self.callsync_interval_spin.value(),
                'teams_enabled': self.teams_enabled_check.isChecked(),
                'teams_tenant_id': self.teams_tenant_edit.text().strip() or None,
                'teams_client_id': self.teams_client_edit.text().strip() or None,
                'teams_client_secret': self.teams_secret_edit.text().strip() or None,
                'placetel_enabled': self.placetel_enabled_check.isChecked(),
                'placetel_api_key': self.placetel_key_edit.text().strip() or None,
                'placetel_api_url': self.placetel_url_edit.text().strip() or 'https://api.placetel.de/v2',
            }

            # Config speichern
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            QMessageBox.information(
                self,
                "Gespeichert",
                "Konfiguration wurde erfolgreich gespeichert!\n\n"
                "Bitte starte den Agent neu, damit die Änderungen aktiv werden."
            )

            self.config_saved.emit()
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Config konnte nicht gespeichert werden:\n{e}")

    def reset_to_defaults(self):
        """Setzt alle Felder auf Standardwerte zurück"""
        reply = QMessageBox.question(
            self,
            "Zurücksetzen",
            "Möchtest du wirklich alle Einstellungen auf die Standardwerte zurücksetzen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            import socket
            hostname = socket.gethostname()

            self.base_url_edit.setText("http://localhost:8000")
            self.user_id_edit.setText("")
            self.machine_id_edit.setText(hostname)
            self.api_key_edit.setText("")
            self.verify_ssl_check.setChecked(False)
            self.poll_interval_spin.setValue(1500)
            self.send_batch_spin.setValue(30)
            self.settings_poll_spin.setValue(60)
            self.include_processes_edit.setPlainText("")
            self.exclude_processes_edit.setPlainText("")
            self.include_keywords_edit.setPlainText("")
            self.exclude_keywords_edit.setPlainText("")
            self.callsync_enabled_check.setChecked(False)
            self.callsync_interval_spin.setValue(15)
            self.teams_enabled_check.setChecked(False)
            self.teams_tenant_edit.setText("")
            self.teams_client_edit.setText("")
            self.teams_secret_edit.setText("")
            self.placetel_enabled_check.setChecked(False)
            self.placetel_key_edit.setText("")
            self.placetel_url_edit.setText("https://api.placetel.de/v2")


def main():
    """Test-Funktion"""
    app = QApplication(sys.argv)

    config_path = Path(__file__).parent / "config.json"
    dialog = ConfigEditorDialog(config_path)
    dialog.exec()

    sys.exit(0)


if __name__ == "__main__":
    main()
