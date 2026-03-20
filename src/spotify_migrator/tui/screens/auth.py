"""Authentication screen."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Header, Input, Static, TextArea


class AuthScreen(Screen):
    """Authentication screen for Spotify OAuth."""

    CSS = """
    AuthScreen {
        background: $surface;
    }

    #auth-container {
        height: 100%;
        width: 100%;
        align: center middle;
    }

    .auth-content {
        width: 80;
        max-width: 700;
    }

    .auth-title {
        text-align: center;
        margin-bottom: 2;
    }

    .auth-instructions {
        margin-bottom: 3;
        color: $text-muted;
    }

    .url-box {
        background: $panel;
        border: solid $primary;
        padding: 2;
        margin-bottom: 3;
    }

    .url-text {
        word-wrap: break-word;
        color: $text;
    }

    .copy-hint {
        margin-bottom: 3;
        color: $accent;
    }

    .input-label {
        margin-bottom: 1;
    }

    TextArea {
        height: 5;
        margin-bottom: 3;
    }

    .button-row {
        width: 100%;
        align: center middle;
    }
    """

    def __init__(self, account: str) -> None:
        super().__init__()
        self.account = account
        self.auth_url: str = ""

    def get_auth_url(self) -> str:
        """Get the authorization URL. Override in subclass."""
        return self.auth_url

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        yield Header()

        with VerticalScroll(id="auth-container"):
            with VerticalScroll(classes="auth-content"):
                account_label = "SOURCE" if self.account == "source" else "TARGET"
                yield Static(f"🔐 Authentification compte {account_label}", classes="auth-title")

                yield Static(
                    "Suivez ces étapes pour vous authentifier:", classes="auth-instructions"
                )

                yield Static("1. Copiez l'URL ci-dessous:", classes="step-label")
                with Vertical(classes="url-box"):
                    yield Static(self.get_auth_url(), classes="url-text", id="auth-url")

                yield Static(
                    "2. Collez l'URL de redirection complète ou le code d'autorisation:",
                    classes="input-label",
                )

                yield TextArea(id="callback-input", placeholder="Collez l'URL ici...")

                yield Static(
                    "💡 Vous pouvez copier l'URL, l'ouvrir dans votre navigateur, "
                    "autoriser l'application, puis copier l'URL de redirection ici.",
                    classes="copy-hint",
                )

                with Horizontal(classes="button-row"):
                    yield Button("← Retour", id="btn-back", variant="default")
                    yield Button("✓ Valider", id="btn-validate", variant="success")
                    yield Button("🔄 Rafraîchir URL", id="btn-refresh", variant="primary")

    @on(Button.Pressed, "#btn-back")
    def on_back(self) -> None:
        """Go back to home screen."""
        self.app.pop_screen()

    def _get_config(self):
        """Get config from store or app."""
        config = getattr(self.app, "_config", None)
        if config is None:
            from spotify_migrator.store import ConfigStore

            config = ConfigStore().load()
        return config

    @on(Button.Pressed, "#btn-refresh")
    def on_refresh(self) -> None:
        """Regenerate auth URL."""
        from spotify_migrator.auth import SpotifyAuthManager, SpotifyAppConfig

        config = self._get_config()
        if config is None:
            self.app.notify(
                "Veuillez d'abord configurer les identifiants dans Setup", severity="warning"
            )
            return

        if self.account == "source":
            app_config = SpotifyAppConfig(
                client_id=config.source_client_id,
                client_secret=config.source_client_secret,
                redirect_uri=config.source_redirect_uri,
            )
        else:
            app_config = SpotifyAppConfig(
                client_id=config.target_client_id,
                client_secret=config.target_client_secret,
                redirect_uri=config.target_redirect_uri,
            )

        auth_manager = SpotifyAuthManager(self.account, app_config)
        self.auth_url = auth_manager.get_authorization_url()

        url_widget = self.query_one("#auth-url", Static)
        url_widget.update(self.auth_url)

    @on(Button.Pressed, "#btn-validate")
    def on_validate(self) -> None:
        """Validate the callback URL."""
        from spotify_migrator.auth import SpotifyAuthManager, SpotifyAppConfig, AuthState
        from spotify_migrator.auth.exceptions import AuthError

        callback_input = self.query_one("#callback-input", TextArea)
        callback_url = callback_input.text

        if not callback_url.strip():
            self.app.notify("Veuillez entrer l'URL de redirection ou le code", severity="warning")
            return

        config = self._get_config()
        if config is None:
            self.app.notify(
                "Veuillez d'abord configurer les identifiants dans Setup", severity="warning"
            )
            return

        if self.account == "source":
            app_config = SpotifyAppConfig(
                client_id=config.source_client_id,
                client_secret=config.source_client_secret,
                redirect_uri=config.source_redirect_uri,
            )
        else:
            app_config = SpotifyAppConfig(
                client_id=config.target_client_id,
                client_secret=config.target_client_secret,
                redirect_uri=config.target_redirect_uri,
            )

        try:
            auth_manager = SpotifyAuthManager(self.account, app_config)
            auth_state = auth_manager.authenticate_with_callback(callback_url)

            self.app.notify(
                f"✓ Authentifié avec succès: {auth_state.display_name}", severity="information"
            )
            self.app.auth_manager_set_state(self.account, auth_state)
            self.app.pop_screen()

        except AuthError as e:
            self.app.notify(f"❌ Erreur: {e.message}", severity="error")


class AuthSourceScreen(AuthScreen):
    """Authentication screen for source account."""

    def __init__(self) -> None:
        super().__init__("source")
        self._load_auth_url()

    def _load_auth_url(self) -> None:
        """Load the authorization URL."""
        from spotify_migrator.auth import SpotifyAuthManager, SpotifyAppConfig
        from spotify_migrator.store import ConfigStore

        config_store = ConfigStore()
        config = config_store.load()

        if config is None:
            self.auth_url = ""
            return

        app_config = SpotifyAppConfig(
            client_id=config.source_client_id,
            client_secret=config.source_client_secret,
            redirect_uri=config.source_redirect_uri,
        )

        auth_manager = SpotifyAuthManager(self.account, app_config)
        self.auth_url = auth_manager.get_authorization_url()

    def get_auth_url(self) -> str:
        """Get the authorization URL."""
        return self.auth_url


class AuthTargetScreen(AuthScreen):
    """Authentication screen for target account."""

    def __init__(self) -> None:
        super().__init__("target")
        self._load_auth_url()

    def _load_auth_url(self) -> None:
        """Load the authorization URL."""
        from spotify_migrator.auth import SpotifyAuthManager, SpotifyAppConfig
        from spotify_migrator.store import ConfigStore

        config_store = ConfigStore()
        config = config_store.load()

        if config is None:
            self.auth_url = ""
            return

        app_config = SpotifyAppConfig(
            client_id=config.target_client_id,
            client_secret=config.target_client_secret,
            redirect_uri=config.target_redirect_uri,
        )

        auth_manager = SpotifyAuthManager(self.account, app_config)
        self.auth_url = auth_manager.get_authorization_url()

    def get_auth_url(self) -> str:
        """Get the authorization URL."""
        return self.auth_url
