"""Logs screen."""

import logging
from io import StringIO

from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Header, Static, Log


class LogsScreen(Screen):
    """Screen showing application logs."""

    CSS = """
    LogsScreen {
        background: $surface;
    }

    #logs-container {
        height: 100%;
        width: 100%;
    }

    .section-title {
        text-align: center;
        margin-bottom: 2;
    }

    .log-section {
        height: 85%;
        border: solid $primary;
    }

    .button-row {
        width: 100%;
        height: auto;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        yield Header()

        with VerticalScroll(id="logs-container"):
            yield Static("📜 Logs de l'application", classes="section-title")

            with VerticalScroll(classes="log-section"):
                yield Log(id="app-log")

            with VerticalScroll(classes="button-row"):
                yield Button("↻ Actualiser", id="btn-refresh", variant="primary")
                yield Button("🗑️ Effacer", id="btn-clear", variant="warning")
                yield Button("← Retour", id="btn-back", variant="default")

    def on_mount(self) -> None:
        """Load logs when screen mounts."""
        self._load_logs()

    def _load_logs(self) -> None:
        """Load and display logs."""
        log_widget = self.query_one("#app-log", Log)

        root_logger = logging.getLogger()
        log_stream = StringIO()

        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                if hasattr(handler, 'stream') and isinstance(handler.stream, StringIO):
                    handler.stream.seek(0)
                    content = handler.stream.read()
                    log_widget.write_line(content)

        log_widget.write_line("=== Configuration ===")
        from dotenv import load_dotenv
        import os
        load_dotenv()

        log_widget.write_line(f"SPOTIFY_SOURCE_CLIENT_ID: {'✓ Configuré' if os.getenv('SPOTIFY_SOURCE_CLIENT_ID') else '✗ Non configuré'}")
        log_widget.write_line(f"SPOTIFY_TARGET_CLIENT_ID: {'✓ Configuré' if os.getenv('SPOTIFY_TARGET_CLIENT_ID') else '✗ Non configuré'}")

    @on(Button.Pressed, "#btn-refresh")
    def on_refresh(self) -> None:
        """Refresh logs."""
        self._load_logs()

    @on(Button.Pressed, "#btn-clear")
    def on_clear(self) -> None:
        """Clear logs."""
        log_widget = self.query_one("#app-log", Log)
        log_widget.clear()

    @on(Button.Pressed, "#btn-back")
    def on_back(self) -> None:
        """Go back to home screen."""
        self.app.pop_screen()
