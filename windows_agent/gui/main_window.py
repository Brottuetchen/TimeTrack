"""
TimeTrack Main Window - Dashboard Container
"""
import logging
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QPushButton,
    QLabel,
)

from .dashboard_widget import DashboardWidget


class MainWindow(QMainWindow):
    """
    Haupt-Dashboard-Fenster mit Tabs.

    Tabs:
        - Dashboard: Live-Event-Preview, Statistiken
        - Einstellungen: Privacy, Whitelist/Blacklist
        - Call-Sync: Status und Konfiguration
    """

    quick_assign_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    privacy_toggle_requested = pyqtSignal(bool)

    def __init__(
        self,
        logger: logging.Logger,
        base_url: str,
        user_id: str,
        api_key: Optional[str] = None,
        verify_ssl: bool = False,
        call_sync_enabled: bool = False
    ):
        super().__init__()
        self.logger = logger
        self.base_url = base_url
        self.user_id = user_id
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.call_sync_enabled = call_sync_enabled

        self.setWindowTitle("TimeTrack Dashboard")
        self.setGeometry(100, 100, 1000, 700)

        # Dark Mode Stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #e0e0e0;
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
            QPushButton:pressed {
                background-color: #0a5a5d;
            }
            QLabel {
                color: #e0e0e0;
            }
            QTableWidget {
                background-color: #2d2d2d;
                color: #e0e0e0;
                gridline-color: #3a3a3a;
                border: 1px solid #3a3a3a;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #3a3a3a;
                color: #e0e0e0;
                padding: 6px;
                border: 1px solid #4a4a4a;
            }
        """)

        # Central Widget mit Tabs
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout(self.central_widget)

        # Header mit Logo und Quick-Actions
        header = self._create_header()
        layout.addWidget(header)

        # Tab Widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Dashboard Tab
        self.dashboard_widget = DashboardWidget(
            logger=logger,
            base_url=base_url,
            user_id=user_id,
            api_key=api_key,
            verify_ssl=verify_ssl
        )
        self.tabs.addTab(self.dashboard_widget, "Dashboard")

        # Call-Sync Tab (nur wenn aktiviert)
        if call_sync_enabled:
            call_sync_tab = self._create_call_sync_tab()
            self.tabs.addTab(call_sync_tab, "Call-Sync")

        self.logger.info("MainWindow initialisiert")

    def _create_header(self) -> QWidget:
        """Erstellt Header mit Logo und Quick-Actions."""
        header = QWidget()
        layout = QHBoxLayout(header)

        # Logo / Title
        title = QLabel("TimeTrack Dashboard")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0d7377;")
        layout.addWidget(title)

        layout.addStretch()

        # Quick-Assign Button
        quick_assign_btn = QPushButton("Quick-Assign")
        quick_assign_btn.clicked.connect(lambda: self.quick_assign_requested.emit())
        layout.addWidget(quick_assign_btn)

        # Settings Button
        settings_btn = QPushButton("Einstellungen")
        settings_btn.clicked.connect(lambda: self.settings_requested.emit())
        layout.addWidget(settings_btn)

        return header

    def _create_call_sync_tab(self) -> QWidget:
        """Erstellt Call-Sync Status Tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info = QLabel("Call-Sync Status wird hier angezeigt")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)

        # TODO: Call-Sync Status Table

        return widget

    def update_dashboard(self, events: list):
        """Update Dashboard mit neuen Events."""
        self.dashboard_widget.update_events(events)

    def update_call_sync_status(self, status: dict):
        """Update Call-Sync Status."""
        # TODO: Update Call-Sync Tab
        pass

    def closeEvent(self, event):
        """Beim Schließen minimieren statt beenden."""
        event.ignore()
        self.hide()
        self.logger.info("Dashboard minimiert")
