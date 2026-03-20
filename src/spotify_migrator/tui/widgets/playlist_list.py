"""Playlist list widget."""

from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static, Button


class PlaylistListItem(Static):
    """A single playlist item in the list."""

    def __init__(self, playlist_id: str, name: str, tracks_count: int, visibility: str) -> None:
        super().__init__()
        self.playlist_id = playlist_id
        self.name = name
        self.tracks_count = tracks_count
        self.visibility = visibility

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        visibility_icon = "🔓" if self.visibility == "public" else "🔒"
        yield Static(
            f"{visibility_icon} {self.name}",
            classes="playlist-name",
        )
        yield Static(
            f"{self.tracks_count} titres",
            classes="playlist-tracks",
        )


class PlaylistList(VerticalScroll):
    """Displays a list of playlists."""

    BINDINGS = [
        ("up", "scroll_up", "Scroll up"),
        ("down", "scroll_down", "Scroll down"),
        ("enter", "select", "Select"),
    ]

    selected_index: int = 0

    def __init__(self) -> None:
        super().__init__()
        self._playlists: list[tuple[str, str, int, str]] = []

    def set_playlists(self, playlists: list[tuple[str, str, int, str]]) -> None:
        """Set the playlists to display."""
        self._playlists = playlists
        self.refresh()

    def get_selected(self) -> tuple[str, str, int, str] | None:
        """Get the currently selected playlist."""
        if 0 <= self.selected_index < len(self._playlists):
            return self._playlists[self.selected_index]
        return None

    def watch_selected_index(self, index: int) -> None:
        """React to selection change."""
        self.scroll_to_row(index, animate=True)

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static("Playlists disponibles", classes="section-title")

        if not self._playlists:
            yield Static("Aucune playlist trouvée", classes="empty-message")
            return

        for i, (pid, name, count, visibility) in enumerate(self._playlists):
            with VerticalScroll(classes="playlist-item", id=f"playlist-{i}"):
                visibility_icon = "🔓" if visibility == "public" else "🔒"
                yield Static(f"{visibility_icon} {name}", classes="playlist-name")
                yield Static(f"{count} titres", classes="playlist-tracks")
