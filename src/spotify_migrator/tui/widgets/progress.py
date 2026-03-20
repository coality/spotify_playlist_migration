"""Progress widgets for TUI."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Gauge, Static


class ProgressDisplay(Widget):
    """Displays migration progress."""

    def __init__(self) -> None:
        super().__init__()
        self.current_track = 0
        self.total_tracks = 0
        self.track_name = ""
        self.playlist_name = ""

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static("", id="progress-playlist-name")
        yield Gauge(id="progress-gauge")
        yield Static("", id="progress-track-info")

    def update(
        self,
        playlist_name: str,
        current_track: int,
        total_tracks: int,
        track_name: str,
    ) -> None:
        """Update progress display."""
        self.playlist_name = playlist_name
        self.current_track = current_track
        self.total_tracks = total_tracks
        self.track_name = track_name

        playlist_label = self.query_one("#progress-playlist-name", Static)
        playlist_label.update(f"[b]Migration:[/b] {playlist_name}")

        gauge = self.query_one("#progress-gauge", Gauge)
        if total_tracks > 0:
            gauge.update(progress=current_track / total_tracks)
        else:
            gauge.update(progress=0)

        track_info = self.query_one("#progress-track-info", Static)
        track_info.update(f"Piste {current_track}/{total_tracks}: {track_name}")


class MigrationResultDisplay(Widget):
    """Displays the result of a migration."""

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static("", id="result-playlist-name")
        yield Static("", id="result-status")
        yield Static("", id="result-tracks-copied")
        yield Static("", id="result-tracks-not-found")
        yield Static("", id="result-error")

    def show_result(
        self,
        playlist_name: str,
        status: str,
        tracks_copied: int,
        tracks_not_found: int,
        error: str | None = None,
    ) -> None:
        """Show a migration result."""
        name = self.query_one("#result-playlist-name", Static)
        name.update(f"[b]{playlist_name}[/b]")

        status_widget = self.query_one("#result-status", Static)
        if status == "completed":
            status_widget.update("[green]✓ Complété[/green]")
        elif status == "skipped":
            status_widget.update("[yellow]⚠ Ignoré[/yellow]")
        else:
            status_widget.update(f"[red]✗ Échoué[/red]")

        copied = self.query_one("#result-tracks-copied", Static)
        copied.update(f"Titres copiés: {tracks_copied}")

        not_found = self.query_one("#result-tracks-not-found", Static)
        not_found.update(f"Titres non trouvés: {tracks_not_found}")

        error_widget = self.query_one("#result-error", Static)
        if error:
            error_widget.update(f"[red]Erreur: {error}[/red]")
        else:
            error_widget.update("")

    def clear(self) -> None:
        """Clear the display."""
        for widget_id in ["result-playlist-name", "result-status", "result-tracks-copied", "result-tracks-not-found", "result-error"]:
            widget = self.query_one(f"#{widget_id}", Static)
            widget.update("")
