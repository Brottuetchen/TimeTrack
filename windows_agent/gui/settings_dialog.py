"""
Settings Dialog für Whitelist/Blacklist, Privacy-Mode, Call-Sync
"""
import logging
from typing import Optional, List

import requests
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QLineEdit,
    QMessageBox,
    QGroupBox,
    QCheckBox,
    QSpinBox,
    QTabWidget,
    QWidget,
)


class SettingsDialog(QDialog):
    """
    Settings Dialog mit Tabs:
    - Privacy & Filter (Whitelist/Blacklist, Privacy-Mode)
    - Call-Sync (Teams/Placetel Settings)
    - Allgemein (Poll-Interval, etc.)
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

        self.current_settings = {}

        self.setWindowTitle("Einstellungen")
        self.setModal(True)
        self.setGeometry(100, 100, 700, 500)

        # Dark Mode
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QLineEdit, QSpinBox {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #3a3a3a;
                padding: 6px;
                border-radius: 4px;
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
            QListWidget {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #3a3a3a;
            }
            QCheckBox {
                color: #e0e0e0;
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
            QTabWidget::pane {
                border: 1px solid #3a3a3a;
                background-color: #2d2d2d;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #e0e0e0;
                padding: 8px 16px;
                border: 1px solid #3a3a3a;
            }
            QTabBar::tab:selected {
                background-color: #0d7377;
                color: white;
            }
        """)

        layout = QVBoxLayout(self)

        # Tab Widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Privacy & Filter Tab
        privacy_tab = self._create_privacy_tab()
        self.tabs.addTab(privacy_tab, "Privacy & Filter")

        # Call-Sync Tab
        call_sync_tab = self._create_call_sync_tab()
        self.tabs.addTab(call_sync_tab, "Call-Sync")

        # Buttons
        buttons = self._create_buttons()
        layout.addWidget(buttons)

        # Settings laden
        self._fetch_settings()

        self.logger.info("SettingsDialog geöffnet")

    def _create_privacy_tab(self) -> QWidget:
        """Erstellt Privacy & Filter Tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Privacy-Mode
        privacy_box = QGroupBox("Privacy-Mode")
        privacy_layout = QVBoxLayout(privacy_box)

        self.privacy_info = QLabel("Lädt...")
        privacy_layout.addWidget(self.privacy_info)

        privacy_buttons = QHBoxLayout()
        self.privacy_pause_btn = QPushButton("30 Min pausieren")
        self.privacy_pause_btn.clicked.connect(lambda: self._set_privacy_mode(30))
        privacy_buttons.addWidget(self.privacy_pause_btn)

        self.privacy_resume_btn = QPushButton("Fortsetzen")
        self.privacy_resume_btn.clicked.connect(lambda: self._set_privacy_mode(0))
        privacy_buttons.addWidget(self.privacy_resume_btn)

        privacy_layout.addLayout(privacy_buttons)
        layout.addWidget(privacy_box)

        # Whitelist
        whitelist_box = QGroupBox("Whitelist (nur diese Prozesse tracken)")
        whitelist_layout = QVBoxLayout(whitelist_box)

        self.whitelist_widget = QListWidget()
        whitelist_layout.addWidget(self.whitelist_widget)

        wl_buttons = QHBoxLayout()
        self.wl_input = QLineEdit()
        self.wl_input.setPlaceholderText("z.B. acad.exe")
        wl_buttons.addWidget(self.wl_input)

        wl_add_btn = QPushButton("Hinzufügen")
        wl_add_btn.clicked.connect(self._add_whitelist)
        wl_buttons.addWidget(wl_add_btn)

        wl_remove_btn = QPushButton("Entfernen")
        wl_remove_btn.clicked.connect(self._remove_whitelist)
        wl_buttons.addWidget(wl_remove_btn)

        whitelist_layout.addLayout(wl_buttons)
        layout.addWidget(whitelist_box)

        # Blacklist
        blacklist_box = QGroupBox("Blacklist (diese Prozesse NICHT tracken)")
        blacklist_layout = QVBoxLayout(blacklist_box)

        self.blacklist_widget = QListWidget()
        blacklist_layout.addWidget(self.blacklist_widget)

        bl_buttons = QHBoxLayout()
        self.bl_input = QLineEdit()
        self.bl_input.setPlaceholderText("z.B. chrome.exe")
        bl_buttons.addWidget(self.bl_input)

        bl_add_btn = QPushButton("Hinzufügen")
        bl_add_btn.clicked.connect(self._add_blacklist)
        bl_buttons.addWidget(bl_add_btn)

        bl_remove_btn = QPushButton("Entfernen")
        bl_remove_btn.clicked.connect(self._remove_blacklist)
        bl_buttons.addWidget(bl_remove_btn)

        blacklist_layout.addLayout(bl_buttons)
        layout.addWidget(blacklist_box)

        return widget

    def _create_call_sync_tab(self) -> QWidget:
        """Erstellt Call-Sync Settings Tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Teams
        teams_box = QGroupBox("Microsoft Teams")
        teams_layout = QVBoxLayout(teams_box)

        self.teams_enabled_cb = QCheckBox("Teams-Synchronisation aktivieren")
        teams_layout.addWidget(self.teams_enabled_cb)

        teams_layout.addWidget(QLabel("Tenant ID:"))
        self.teams_tenant_input = QLineEdit()
        teams_layout.addWidget(self.teams_tenant_input)

        teams_layout.addWidget(QLabel("Client ID:"))
        self.teams_client_input = QLineEdit()
        teams_layout.addWidget(self.teams_client_input)

        teams_layout.addWidget(QLabel("Client Secret:"))
        self.teams_secret_input = QLineEdit()
        self.teams_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        teams_layout.addWidget(self.teams_secret_input)

        layout.addWidget(teams_box)

        # Placetel
        placetel_box = QGroupBox("Placetel")
        placetel_layout = QVBoxLayout(placetel_box)

        self.placetel_enabled_cb = QCheckBox("Placetel-Synchronisation aktivieren")
        placetel_layout.addWidget(self.placetel_enabled_cb)

        placetel_layout.addWidget(QLabel("API-Key:"))
        self.placetel_key_input = QLineEdit()
        self.placetel_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        placetel_layout.addWidget(self.placetel_key_input)

        layout.addWidget(placetel_box)

        layout.addStretch()

        return widget

    def _create_buttons(self) -> QWidget:
        """Erstellt Button-Leiste."""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        layout.addStretch()

        # Abbrechen
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        # Speichern
        save_btn = QPushButton("Speichern")
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)

        return widget

    def _fetch_settings(self):
        """Lädt Settings vom Backend."""
        try:
            url = f"{self.base_url}/settings/logging"
            resp = self.session.get(url, verify=self.verify_ssl, timeout=5)

            if resp.status_code == 200:
                self.current_settings = resp.json()
                self._populate_settings()
            else:
                self.logger.warning(f"Settings laden fehlgeschlagen: {resp.status_code}")

        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Settings: {e}")

    def _populate_settings(self):
        """Füllt UI mit Settings."""
        # Privacy-Mode
        privacy_until = self.current_settings.get("privacy_mode_until")
        if not privacy_until:
            self.privacy_info.setText("Privacy-Mode: AKTIV (Tracking läuft)")
        elif privacy_until == "indefinite":
            self.privacy_info.setText("Privacy-Mode: PAUSIERT (unbegrenzt)")
        else:
            self.privacy_info.setText(f"Privacy-Mode: PAUSIERT bis {privacy_until}")

        # Whitelist
        self.whitelist_widget.clear()
        whitelist = self.current_settings.get("whitelist", [])
        for item in whitelist:
            self.whitelist_widget.addItem(item)

        # Blacklist
        self.blacklist_widget.clear()
        blacklist = self.current_settings.get("blacklist", [])
        for item in blacklist:
            self.blacklist_widget.addItem(item)

        # Call-Sync
        self.teams_enabled_cb.setChecked(
            self.current_settings.get("teams_tenant_id") is not None
        )
        self.teams_tenant_input.setText(
            self.current_settings.get("teams_tenant_id") or ""
        )
        self.teams_client_input.setText(
            self.current_settings.get("teams_client_id") or ""
        )
        self.teams_secret_input.setText(
            self.current_settings.get("teams_client_secret") or ""
        )

        self.placetel_enabled_cb.setChecked(
            self.current_settings.get("placetel_shared_secret") is not None
        )
        self.placetel_key_input.setText(
            self.current_settings.get("placetel_shared_secret") or ""
        )

    def _add_whitelist(self):
        """Fügt Whitelist-Eintrag hinzu."""
        text = self.wl_input.text().strip().lower()
        if text:
            self.whitelist_widget.addItem(text)
            self.wl_input.clear()

    def _remove_whitelist(self):
        """Entfernt Whitelist-Eintrag."""
        current = self.whitelist_widget.currentRow()
        if current >= 0:
            self.whitelist_widget.takeItem(current)

    def _add_blacklist(self):
        """Fügt Blacklist-Eintrag hinzu."""
        text = self.bl_input.text().strip().lower()
        if text:
            self.blacklist_widget.addItem(text)
            self.bl_input.clear()

    def _remove_blacklist(self):
        """Entfernt Blacklist-Eintrag."""
        current = self.blacklist_widget.currentRow()
        if current >= 0:
            self.blacklist_widget.takeItem(current)

    def _set_privacy_mode(self, minutes: int):
        """Setzt Privacy-Mode."""
        try:
            url = f"{self.base_url}/settings/privacy-mode"
            payload = {"duration_minutes": minutes}
            resp = self.session.post(url, json=payload, verify=self.verify_ssl, timeout=5)

            if resp.status_code == 200:
                if minutes == 0:
                    QMessageBox.information(self, "Erfolg", "Privacy-Mode beendet")
                else:
                    QMessageBox.information(self, "Erfolg", f"Privacy-Mode für {minutes} Minuten aktiviert")
                self._fetch_settings()
            else:
                QMessageBox.warning(self, "Fehler", f"Privacy-Mode konnte nicht gesetzt werden: {resp.status_code}")

        except Exception as e:
            self.logger.error(f"Fehler beim Setzen des Privacy-Mode: {e}")
            QMessageBox.critical(self, "Fehler", f"Fehler:\n{str(e)}")

    def _save_settings(self):
        """Speichert Settings."""
        try:
            # Whitelist/Blacklist sammeln
            whitelist = [
                self.whitelist_widget.item(i).text()
                for i in range(self.whitelist_widget.count())
            ]
            blacklist = [
                self.blacklist_widget.item(i).text()
                for i in range(self.blacklist_widget.count())
            ]

            # Settings updaten
            settings = {**self.current_settings}
            settings["whitelist"] = whitelist
            settings["blacklist"] = blacklist

            # Call-Sync
            if self.teams_enabled_cb.isChecked():
                settings["teams_tenant_id"] = self.teams_tenant_input.text().strip()
                settings["teams_client_id"] = self.teams_client_input.text().strip()
                settings["teams_client_secret"] = self.teams_secret_input.text().strip()
            else:
                settings["teams_tenant_id"] = None
                settings["teams_client_id"] = None
                settings["teams_client_secret"] = None

            if self.placetel_enabled_cb.isChecked():
                settings["placetel_shared_secret"] = self.placetel_key_input.text().strip()
            else:
                settings["placetel_shared_secret"] = None

            # POST an Backend
            url = f"{self.base_url}/settings/logging"
            resp = self.session.post(url, json=settings, verify=self.verify_ssl, timeout=10)

            if resp.status_code == 200:
                QMessageBox.information(self, "Erfolg", "Einstellungen gespeichert")
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    "Fehler",
                    f"Speichern fehlgeschlagen: {resp.status_code}\n{resp.text}"
                )

        except Exception as e:
            self.logger.exception(f"Fehler beim Speichern: {e}")
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern:\n{str(e)}")
