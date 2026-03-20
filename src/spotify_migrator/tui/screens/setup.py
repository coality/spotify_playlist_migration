"""Setup screen for configuring Spotify API credentials."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Header, Input, Static


INSTRUCTIONS = """
Pour utiliser cette application, vous devez créer une application Spotify Developer.

[b]Étape 1:[/b] Allez sur https://developer.spotify.com/dashboard

[b]Étape 2:[/b] Cliquez sur "Create App"

[b]Étape 3:[/b] Donnez un nom à votre application (ex: "Spotify Migrator")

[b]Étape 4:[/b] Remplissez les champs:
  - Website: http://localhost:8080
  - Redirect URIs: http://localhost:8080
  - Installer Types: Native

[b]Étape 5:[/b] Cliquez sur "Save"

[b]Étape 6:[/b] Dans votre app, allez dans "Settings" en haut à droite

[b]Étape 7:[/b] Copiez le "Client ID" et le "Client Secret"

Vous devrez créer DEUX applications Spotify (une pour le compte source et une pour le compte target).
"""


class SetupScreen(Screen):
    """Screen for initial setup of Spotify credentials."""

    CSS = """
    SetupScreen {
        background: $surface;
    }

    #setup-container {
        height: 100%;
        width: 100%;
    }

    .setup-content {
        width: 100%;
        height: 100%;
    }

    .section {
        margin-bottom: 2;
        padding: 1;
        border: solid $primary 30%;
    }

    .section-title {
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }

    .section-description {
        color: $text-muted;
        margin-bottom: 1;
    }

    .input-row {
        height: auto;
        margin-bottom: 1;
    }

    .input-label {
        color: $text-muted;
        margin-bottom: 0;
    }

    Input {
        margin-bottom: 1;
    }

    .instructions-box {
        background: $panel;
        padding: 1;
        margin-bottom: 2;
    }

    .instructions-text {
        color: $text;
    }

    .button-row {
        height: auto;
        width: 100%;
        align: center middle;
    }

    .nav-hint {
        color: $text-muted;
        text-align: center;
        margin-top: 1;
    }
    """

    BINDING_TEXT = "Appuyez sur Ctrl+C pour coller depuis le presse-papier"

    def __init__(self, from_home: bool = False) -> None:
        super().__init__()
        self.from_home = from_home

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        yield Header()

        with VerticalScroll(id="setup-container"):
            with VerticalScroll(classes="setup-content"):
                yield Static("⚙️ Configuration Spotify", classes="menu-title")
                yield Static(
                    "Entrez vos identifiants Spotify Developer pour configurer l'application.",
                    classes="menu-subtitle",
                )

                with Vertical(classes="instructions-box"):
                    yield Static(INSTRUCTIONS, classes="instructions-text", id="instructions")

                yield Static("📱 Compte SOURCE (ancien compte)", classes="section-title")

                with Vertical(classes="section"):
                    yield Static("Client ID (SPOTIFY_SOURCE_CLIENT_ID):", classes="input-label")
                    yield Input(id="source-client-id", placeholder="ex: 1a2b3c4d5e6f7g8h9i0j...")

                    yield Static(
                        "Client Secret (SPOTIFY_SOURCE_CLIENT_SECRET):", classes="input-label"
                    )
                    yield Input(
                        id="source-client-secret", placeholder="ex: 1a2b3c4d5e6f...", password=True
                    )

                    yield Static("Redirect URI:", classes="input-label")
                    yield Input(
                        id="source-redirect-uri",
                        value="http://localhost:8080",
                        placeholder="http://localhost:8080",
                    )

                yield Static("📱 Compte TARGET (nouveau compte)", classes="section-title")

                with Vertical(classes="section"):
                    yield Static("Client ID (SPOTIFY_TARGET_CLIENT_ID):", classes="input-label")
                    yield Input(id="target-client-id", placeholder="ex: 1a2b3c4d5e6f7g8h9i0j...")

                    yield Static(
                        "Client Secret (SPOTIFY_TARGET_CLIENT_SECRET):", classes="input-label"
                    )
                    yield Input(
                        id="target-client-secret", placeholder="ex: 1a2b3c4d5e6f...", password=True
                    )

                    yield Static("Redirect URI:", classes="input-label")
                    yield Input(
                        id="target-redirect-uri",
                        value="http://localhost:8080",
                        placeholder="http://localhost:8080",
                    )

                with Horizontal(classes="button-row"):
                    yield Button("← Retour", id="btn-back", variant="default")
                    yield Button("✓ Enregistrer", id="btn-save", variant="success")

                yield Static(self.BINDING_TEXT, classes="nav-hint")

    @on(Button.Pressed, "#btn-back")
    def on_back(self) -> None:
        """Go back."""
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-save")
    def on_save(self) -> None:
        """Save the configuration."""
        from spotify_migrator.store import ConfigStore, AppConfig

        source_client_id = self.query_one("#source-client-id", Input).value.strip()
        source_client_secret = self.query_one("#source-client-secret", Input).value.strip() or None
        source_redirect_uri = self.query_one("#source-redirect-uri", Input).value.strip()

        target_client_id = self.query_one("#target-client-id", Input).value.strip()
        target_client_secret = self.query_one("#target-client-secret", Input).value.strip() or None
        target_redirect_uri = self.query_one("#target-redirect-uri", Input).value.strip()

        if not source_client_id:
            self.app.notify("Client ID source requis", severity="warning")
            return
        if not target_client_id:
            self.app.notify("Client ID target requis", severity="warning")
            return
        if not source_redirect_uri:
            source_redirect_uri = "http://localhost:8080"
        if not target_redirect_uri:
            target_redirect_uri = "http://localhost:8080"

        config = AppConfig(
            source_client_id=source_client_id,
            source_client_secret=source_client_secret,
            source_redirect_uri=source_redirect_uri,
            target_client_id=target_client_id,
            target_client_secret=target_client_secret,
            target_redirect_uri=target_redirect_uri,
        )

        store = ConfigStore()
        store.save(config)

        self.app.notify("Configuration enregistrée avec succès!", severity="information")

        if self.from_home:
            self.app.pop_screen()
        else:
            self.app.pop_screen()
            self.app.push_screen("home")
