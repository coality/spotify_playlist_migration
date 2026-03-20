"""Main TUI application."""

import logging
import os
from typing import Any

from textual.app import App
from textual.driver import Driver
from textual.pilot import Pilot

from spotify_migrator.auth import AuthState
from spotify_migrator.tui.screens import (
    HomeScreen,
    AuthSourceScreen,
    AuthTargetScreen,
    PlaylistsScreen,
    MigrateOneScreen,
    MigrateAllScreen,
    LogsScreen,
    SetupScreen,
)

logger = logging.getLogger(__name__)


class SpotifyMigratorApp(App):
    """Main TUI application for Spotify Playlist Migrator."""

    CSS = """
    Screen {
        background: $surface;
    }

    .menu-title {
        color: $accent;
        text-style: bold;
    }

    .menu-subtitle {
        color: $text-muted;
    }

    .status-title {
        color: $primary;
        margin-bottom: 1;
    }

    .account-status {
        color: $text;
    }

    .section-title {
        color: $accent;
        text-style: bold;
    }

    .hint {
        color: $text-muted;
    }

    .empty-message {
        color: $text-muted;
        text-align: center;
        padding: 2;
    }

    Button {
        min-width: 20;
    }

    .button-row {
        height: auto;
        width: 100%;
    }
    """

    SCREENS = {
        "home": HomeScreen,
        "auth_source": AuthSourceScreen,
        "auth_target": AuthTargetScreen,
        "playlists": PlaylistsScreen,
        "migrate_one": MigrateOneScreen,
        "migrate_all": MigrateAllScreen,
        "logs": LogsScreen,
        "setup": SetupScreen,
    }

    def __init__(self, driver_class: type[Driver] | None = None, **kwargs: Any) -> None:
        super().__init__(driver_class=driver_class, **kwargs)
        self._source_auth_state: AuthState | None = None
        self._target_auth_state: AuthState | None = None
        self.selected_playlist: tuple[str, str, int, str] | None = None

        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup application logging."""
        from dotenv import load_dotenv

        load_dotenv()

        log_level_str = os.getenv("LOG_LEVEL", "INFO")
        log_level = getattr(logging, log_level_str.upper(), logging.INFO)

        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def on_mount(self) -> None:
        """Handle app mount."""
        from spotify_migrator.store import ConfigStore

        config_store = ConfigStore()
        config = config_store.load()

        if config is None:
            self.push_screen("setup")
        else:
            self._config = config
            self._check_auth_states()
            self.push_screen("home")

    def _check_auth_states(self) -> None:
        """Check authentication states for both accounts."""
        from spotify_migrator.auth import SpotifyAuthManager, SpotifyAppConfig

        config = getattr(self, "_config", None)
        if config is None:
            from spotify_migrator.store import ConfigStore

            config = ConfigStore().load()
            self._config = config

        if config is None:
            return

        try:
            source_config = SpotifyAppConfig(
                client_id=config.source_client_id,
                client_secret=config.source_client_secret,
                redirect_uri=config.source_redirect_uri,
            )
            source_auth = SpotifyAuthManager("source", source_config)
            self._source_auth_state = source_auth.load_cached_auth()
        except Exception as e:
            logger.warning(f"Could not check source auth: {e}")
            self._source_auth_state = None

        try:
            target_config = SpotifyAppConfig(
                client_id=config.target_client_id,
                client_secret=config.target_client_secret,
                redirect_uri=config.target_redirect_uri,
            )
            target_auth = SpotifyAuthManager("target", target_config)
            self._target_auth_state = target_auth.load_cached_auth()
        except Exception as e:
            logger.warning(f"Could not check target auth: {e}")
            self._target_auth_state = None

    def auth_manager_set_state(self, account: str, state: AuthState) -> None:
        """Set authentication state for an account."""
        if account == "source":
            self._source_auth_state = state
        elif account == "target":
            self._target_auth_state = state

        logger.info(f"Auth state updated for {account}: {state.is_authenticated}")

    def is_source_authenticated(self) -> bool:
        """Check if source account is authenticated."""
        return self._source_auth_state is not None and self._source_auth_state.is_authenticated

    def is_target_authenticated(self) -> bool:
        """Check if target account is authenticated."""
        return self._target_auth_state is not None and self._target_auth_state.is_authenticated

    def get_source_name(self) -> str | None:
        """Get source account display name."""
        if self._source_auth_state:
            return self._source_auth_state.display_name
        return None

    def get_target_name(self) -> str | None:
        """Get target account display name."""
        if self._target_auth_state:
            return self._target_auth_state.display_name
        return None


def main() -> None:
    """Main entry point."""
    app = SpotifyMigratorApp()
    app.title = "Spotify Playlist Migrator"
    app.run()


if __name__ == "__main__":
    main()
