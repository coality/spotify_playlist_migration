"""Playlists list screen."""

from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Header, Static


class PlaylistsScreen(Screen):
    """Screen showing source playlists."""

    CSS = """
    PlaylistsScreen {
        background: $surface;
    }

    #playlists-container {
        height: 100%;
        width: 100%;
    }

    .section-title {
        text-align: center;
        margin-bottom: 2;
    }

    .playlists-list {
        height: 70%;
        border: solid $primary;
        margin-bottom: 2;
    }

    .playlist-item {
        height: auto;
        padding: 1;
        border-bottom: solid $border 20%;
    }

    .playlist-name {
        color: $text;
    }

    .playlist-tracks {
        color: $text-muted;
        font-size: 0.8em;
    }

    .button-row {
        width: 100%;
        height: auto;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._playlists: list[tuple[str, str, int, str]] = []

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        yield Header()

        with VerticalScroll(id="playlists-container"):
            yield Static("📋 Playlists du compte SOURCE", classes="section-title")
            yield Static("Appuyez sur Entrée ou cliquez pour sélectionner", classes="hint")

            yield VerticalScroll(classes="playlists-list", id="playlists-list")

            with VerticalScroll(classes="button-row"):
                yield Button("← Retour", id="btn-back", variant="default")
                yield Button(
                    "📤 Migrer la sélectionnée", id="btn-migrate", variant="success", disabled=True
                )

    def on_mount(self) -> None:
        """Load playlists when screen mounts."""
        self._load_playlists()

    def _load_playlists(self) -> None:
        """Load playlists from source account."""
        from spotify_migrator.auth import SpotifyAuthManager, SpotifyAppConfig, AuthState
        from spotify_migrator.api import SpotifyAPIClient
        from spotify_migrator.store import ConfigStore

        try:
            config_store = ConfigStore()
            config = config_store.load()

            if config is None:
                self.app.notify("Veuillez configurer les identifiants Spotify", severity="warning")
                self.app.push_screen("setup")
                return

            app_config = SpotifyAppConfig(
                client_id=config.source_client_id,
                client_secret=config.source_client_secret,
                redirect_uri=config.source_redirect_uri,
            )

            auth_manager = SpotifyAuthManager("source", app_config)
            auth_state = auth_manager.load_cached_auth()

            if not auth_state or not auth_state.is_authenticated:
                self.app.notify("Non connecté au compte source", severity="warning")
                self.app.pop_screen()
                return

            sp = auth_manager.get_client()
            api_client = SpotifyAPIClient(sp)

            playlists = list(api_client.get_user_playlists())
            self._playlists = [
                (p.id, p.name, p.tracks_count, p.visibility.value) for p in playlists
            ]

            self._update_list()

        except Exception as e:
            self.app.notify(f"Erreur: {e}", severity="error")
            self.app.pop_screen()

    def _update_list(self) -> None:
        """Update the playlists list display."""
        container = self.query_one("#playlists-list", VerticalScroll)
        container.remove_children()

        if not self._playlists:
            container.mount(Static("Aucune playlist trouvée", classes="empty-message"))
            return

        for i, (pid, name, count, visibility) in enumerate(self._playlists):
            icon = "🔓" if visibility == "public" else "🔒"
            container.mount(
                Static(f"{icon} {name}", classes="playlist-name"),
            )
            container.mount(
                Static(f"   {count} titres • {visibility}", classes="playlist-tracks"),
            )

    @on(Button.Pressed, "#btn-back")
    def on_back(self) -> None:
        """Go back to home screen."""
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-migrate")
    def on_migrate(self) -> None:
        """Migrate selected playlist."""
        selected = self._get_selected_playlist()
        if selected:
            self.app.selected_playlist = selected
            self.app.push_screen("migrate_one")

    def _get_selected_playlist(self) -> tuple[str, str, int, str] | None:
        """Get the selected playlist from the list."""
        return None
