"""Tests for TUI application."""

import pytest
from unittest.mock import MagicMock, patch

from spotify_migrator.auth import AuthState


class TestSpotifyMigratorApp:
    """Tests for SpotifyMigratorApp."""

    def test_app_init(self):
        """Test app initialization."""
        from spotify_migrator.tui import SpotifyMigratorApp

        app = SpotifyMigratorApp()

        assert app._source_auth_state is None
        assert app._target_auth_state is None
        assert app.selected_playlist is None

    def test_is_source_authenticated_false(self):
        """Test is_source_authenticated returns False when not authenticated."""
        from spotify_migrator.tui import SpotifyMigratorApp

        app = SpotifyMigratorApp()
        assert app.is_source_authenticated() is False

    def test_is_target_authenticated_false(self):
        """Test is_target_authenticated returns False when not authenticated."""
        from spotify_migrator.tui import SpotifyMigratorApp

        app = SpotifyMigratorApp()
        assert app.is_target_authenticated() is False

    def test_is_source_authenticated_true(self, auth_state_authenticated):
        """Test is_source_authenticated returns True when authenticated."""
        from spotify_migrator.tui import SpotifyMigratorApp

        app = SpotifyMigratorApp()
        app._source_auth_state = auth_state_authenticated
        assert app.is_source_authenticated() is True

    def test_is_target_authenticated_true(self, auth_state_authenticated):
        """Test is_target_authenticated returns True when authenticated."""
        from spotify_migrator.tui import SpotifyMigratorApp

        app = SpotifyMigratorApp()
        app._target_auth_state = auth_state_authenticated
        assert app.is_target_authenticated() is True

    def test_get_source_name(self, auth_state_authenticated):
        """Test get_source_name returns display name."""
        from spotify_migrator.tui import SpotifyMigratorApp

        app = SpotifyMigratorApp()
        app._source_auth_state = auth_state_authenticated
        assert app.get_source_name() == "Test User"

    def test_get_target_name(self, auth_state_authenticated):
        """Test get_target_name returns display name."""
        from spotify_migrator.tui import SpotifyMigratorApp

        app = SpotifyMigratorApp()
        app._target_auth_state = auth_state_authenticated
        assert app.get_target_name() == "Test User"

    def test_auth_manager_set_state_source(self, auth_state_authenticated):
        """Test setting auth state for source account."""
        from spotify_migrator.tui import SpotifyMigratorApp

        app = SpotifyMigratorApp()
        app.auth_manager_set_state("source", auth_state_authenticated)

        assert app._source_auth_state == auth_state_authenticated

    def test_auth_manager_set_state_target(self, auth_state_authenticated):
        """Test setting auth state for target account."""
        from spotify_migrator.tui import SpotifyMigratorApp

        app = SpotifyMigratorApp()
        app.auth_manager_set_state("target", auth_state_authenticated)

        assert app._target_auth_state == auth_state_authenticated


class TestHomeScreen:
    """Tests for HomeScreen."""

    def test_home_screen_composes(self):
        """Test that HomeScreen can compose."""
        from textual.pilot import Pilot
        from spotify_migrator.tui.screens import HomeScreen

        screen = HomeScreen()
        assert screen is not None

    def test_home_screen_with_auth_state(self):
        """Test HomeScreen with authentication states."""
        from spotify_migrator.tui.screens import HomeScreen

        screen = HomeScreen(
            source_authenticated=True,
            target_authenticated=True,
            source_name="Source User",
            target_name="Target User",
        )

        assert screen.source_authenticated is True
        assert screen.target_authenticated is True
        assert screen.source_name == "Source User"
        assert screen.target_name == "Target User"


class TestAuthScreen:
    """Tests for AuthScreen."""

    def test_auth_source_screen_init(self):
        """Test AuthSourceScreen initialization."""
        from spotify_migrator.tui.screens import AuthSourceScreen

        with patch("spotify_migrator.auth.SpotifyAuthManager"):
            screen = AuthSourceScreen()
            assert screen.account == "source"

    def test_auth_target_screen_init(self):
        """Test AuthTargetScreen initialization."""
        from spotify_migrator.tui.screens import AuthTargetScreen

        with patch("spotify_migrator.auth.SpotifyAuthManager"):
            screen = AuthTargetScreen()
            assert screen.account == "target"


class TestPlaylistScreen:
    """Tests for PlaylistsScreen."""

    def test_playlists_screen_init(self):
        """Test PlaylistsScreen initialization."""
        from spotify_migrator.tui.screens import PlaylistsScreen

        screen = PlaylistsScreen()
        assert screen._playlists == []


class TestMigrateScreens:
    """Tests for Migrate screens."""

    def test_migrate_one_screen_init(self):
        """Test MigrateOneScreen initialization."""
        from spotify_migrator.tui.screens import MigrateOneScreen

        screen = MigrateOneScreen()
        assert screen.playlist_name is None
        assert screen.is_migrating is False

    def test_migrate_one_screen_with_playlist_name(self):
        """Test MigrateOneScreen with playlist name."""
        from spotify_migrator.tui.screens import MigrateOneScreen

        screen = MigrateOneScreen(playlist_name="My Playlist")
        assert screen.playlist_name == "My Playlist"

    def test_migrate_all_screen_init(self):
        """Test MigrateAllScreen initialization."""
        from spotify_migrator.tui.screens import MigrateAllScreen

        screen = MigrateAllScreen()
        assert screen.is_migrating is False


class TestLogsScreen:
    """Tests for LogsScreen."""

    def test_logs_screen_init(self):
        """Test LogsScreen initialization."""
        from spotify_migrator.tui.screens import LogsScreen

        screen = LogsScreen()
        assert screen is not None
