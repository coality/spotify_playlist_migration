"""Status widgets for TUI."""

from datetime import datetime
from typing import Callable

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Static


class AccountStatus(Widget):
    """Displays authentication status for an account."""

    account: reactive[str] = reactive("")
    is_authenticated: reactive[bool] = reactive(False)
    display_name: reactive[str | None] = reactive(None)
    needs_refresh: reactive[bool] = reactive(False)

    def __init__(self, account: str, label: str) -> None:
        super().__init__()
        self.account = account
        self.label = label

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        with Horizontal(classes="status-row"):
            yield Static(f"[b]{self.label}[/b]", classes="status-label")
            yield Static("", id="status-indicator")

    def watch_is_authenticated(self, authenticated: bool) -> None:
        """Update indicator when authentication state changes."""
        indicator = self.query_one("#status-indicator", Static)

        if authenticated:
            if self.needs_refresh:
                indicator.update(f"[yellow]⚠ Token expiré[/yellow]")
            else:
                name = self.display_name or "Connected"
                indicator.update(f"[green]✓ {name}[/green]")
        else:
            indicator.update("[red]✗ Non connecté[/red]")


class StatusBar(Widget):
    """Status bar showing connection status for both accounts."""

    def __init__(self, source_status: Callable[[], bool], target_status: Callable[[], bool]) -> None:
        super().__init__()
        self._source_status = source_status
        self._target_status = target_status

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        with Horizontal(id="status-bar"):
            yield Static("Source: ", classes="status-label")
            yield Static("---", id="source-indicator", classes="status-indicator")
            yield Static(" | ", classes="status-separator")
            yield Static("Target: ", classes="status-label")
            yield Static("---", id="target-indicator", classes="status-indicator")

    def update_status(self, source_auth: bool, target_auth: bool) -> None:
        """Update status indicators."""
        source = self.query_one("#source-indicator", Static)
        target = self.query_one("#target-indicator", Static)

        source.update("[green]✓[/green]" if source_auth else "[red]✗[/red]")
        target.update("[green]✓[/green]" if target_auth else "[red]✗[/red]")
