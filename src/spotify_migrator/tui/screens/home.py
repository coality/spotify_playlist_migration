"""Home screen."""

from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Header, Static


class HomeScreen(Screen):
    """Main menu screen."""

    CSS = """
    Screen {
        background: $surface;
    }

    #menu-container {
        height: 100%;
        width: 100%;
        align: center middle;
    }

    .menu-title {
        width: 100%;
        text-align: center;
        margin-bottom: 2;
    }

    .menu-subtitle {
        width: 100%;
        text-align: center;
        margin-bottom: 3;
        color: $text-muted;
    }

    .menu-buttons {
        width: 50;
        max-width: 400;
    }

    Button {
        width: 100%;
        margin-bottom: 1;
    }

    .status-summary {
        width: 100%;
        text-align: center;
        margin-top: 3;
        padding-top: 2;
        border-top: solid $primary 30%;
    }

    .account-status {
        margin-bottom: 1;
    }
    """

    def __init__(
        self,
        source_authenticated: bool = False,
        target_authenticated: bool = False,
        source_name: str | None = None,
        target_name: str | None = None,
    ) -> None:
        super().__init__()
        self.source_authenticated = source_authenticated
        self.target_authenticated = target_authenticated
        self.source_name = source_name
        self.target_name = target_name

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        yield Header()

        with VerticalScroll(id="menu-container"):
            with VerticalScroll(classes="menu-buttons"):
                yield Static("🎵 Spotify Playlist Migrator", classes="menu-title")
                yield Static(
                    "Migration de playlists entre comptes Spotify", classes="menu-subtitle"
                )

                yield Button(
                    "🔐 Authentifier compte SOURCE", id="btn-auth-source", variant="primary"
                )
                yield Button(
                    "🔐 Authentifier compte TARGET", id="btn-auth-target", variant="primary"
                )

                yield Button("📋 Lister les playlists source", id="btn-list-playlists")
                yield Button("📤 Migrer une playlist", id="btn-migrate-one")
                yield Button("📤 Migrer toutes les playlists", id="btn-migrate-all")

                yield Button("⚙️ Configurer identifiants Spotify", id="btn-setup", variant="default")
                yield Button("📜 Voir les logs", id="btn-view-logs")
                yield Button("❌ Quitter", id="btn-quit", variant="error")

            with VerticalScroll(classes="status-summary"):
                yield Static("[b]État des connexions[/b]", classes="status-title")

                source_status = (
                    "[green]✓ Connecté" if self.source_authenticated else "[red]✗ Non connecté"
                )
                if self.source_name:
                    source_status += f" ({self.source_name})"
                yield Static(f"Source: {source_status}", classes="account-status")

                target_status = (
                    "[green]✓ Connecté" if self.target_authenticated else "[red]✗ Non connecté"
                )
                if self.target_name:
                    target_status += f" ({self.target_name})"
                yield Static(f"Target: {target_status}", classes="account-status")

    @on(Button.Pressed, "#btn-auth-source")
    def on_auth_source(self) -> None:
        """Navigate to source authentication."""
        self.app.push_screen("auth_source")

    @on(Button.Pressed, "#btn-auth-target")
    def on_auth_target(self) -> None:
        """Navigate to target authentication."""
        self.app.push_screen("auth_target")

    @on(Button.Pressed, "#btn-list-playlists")
    def on_list_playlists(self) -> None:
        """Navigate to playlist list."""
        if not self.source_authenticated:
            self.app.notify(
                "Veuillez d'abord vous authentifier au compte source", severity="warning"
            )
            return
        self.app.push_screen("playlists")

    @on(Button.Pressed, "#btn-migrate-one")
    def on_migrate_one(self) -> None:
        """Navigate to migrate one playlist."""
        if not self.source_authenticated:
            self.app.notify(
                "Veuillez d'abord vous authentifier au compte source", severity="warning"
            )
            return
        if not self.target_authenticated:
            self.app.notify(
                "Veuillez d'abord vous authentifier au compte target", severity="warning"
            )
            return
        self.app.push_screen("migrate_one")

    @on(Button.Pressed, "#btn-migrate-all")
    def on_migrate_all(self) -> None:
        """Navigate to migrate all playlists."""
        if not self.source_authenticated:
            self.app.notify(
                "Veuillez d'abord vous authentifier au compte source", severity="warning"
            )
            return
        if not self.target_authenticated:
            self.app.notify(
                "Veuillez d'abord vous authentifier au compte target", severity="warning"
            )
            return
        self.app.push_screen("migrate_all")

    @on(Button.Pressed, "#btn-view-logs")
    def on_view_logs(self) -> None:
        """Navigate to logs screen."""
        self.app.push_screen("logs")

    @on(Button.Pressed, "#btn-setup")
    def on_setup(self) -> None:
        """Navigate to setup screen."""
        self.app.push_screen("setup")

    @on(Button.Pressed, "#btn-quit")
    def on_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
