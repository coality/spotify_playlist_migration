"""Tests for AuthManager."""

import pytest
from unittest.mock import MagicMock, patch

from spotify_migrator.auth import (
    SpotifyAuthManager,
    SpotifyAppConfig,
    AuthState,
)
from spotify_migrator.auth.exceptions import (
    AuthenticationFailedError,
    AuthorizationError,
    InvalidTokenError,
)


class TestSpotifyAppConfig:
    """Tests for SpotifyAppConfig."""

    def test_has_client_secret_true(self):
        """Test has_client_secret returns True when secret is set."""
        config = SpotifyAppConfig(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8080",
        )
        assert config.has_client_secret() is True

    def test_has_client_secret_false(self):
        """Test has_client_secret returns False when secret is None."""
        config = SpotifyAppConfig(
            client_id="test_id",
            client_secret=None,
            redirect_uri="http://localhost:8080",
        )
        assert config.has_client_secret() is False


class TestSpotifyAuthManager:
    """Tests for SpotifyAuthManager."""

    def test_init_sets_account(self, source_config):
        """Test __init__ sets account name."""
        auth = SpotifyAuthManager("source", source_config)
        assert auth.account == "source"

    def test_init_sets_config(self, source_config):
        """Test __init__ sets config."""
        auth = SpotifyAuthManager("source", source_config)
        assert auth.config == source_config

    def test_get_authorization_url(self, source_config):
        """Test get_authorization_url returns a URL."""
        auth = SpotifyAuthManager("source", source_config)

        with patch.object(auth, '_create_auth_manager') as mock_auth:
            mock_auth.return_value.get_authorize_url.return_value = "https://accounts.spotify.com/authorize?client_id=test"
            url = auth.get_authorization_url()
            assert url == "https://accounts.spotify.com/authorize?client_id=test"


class TestCallbackParsing:
    """Tests for callback URL parsing."""

    def test_parse_full_callback_url(self):
        """Test parsing a full callback URL with code."""
        from spotify_migrator.auth.manager import SpotifyAuthManager

        config = SpotifyAppConfig(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8080",
        )
        auth = SpotifyAuthManager("source", config)

        callback = "http://localhost:8080/?code=abc123def456&state=xyz"
        result = auth._parse_callback_url(callback)

        assert result == "abc123def456"

    def test_parse_callback_url_with_error(self):
        """Test parsing callback URL with error (access_denied)."""
        from spotify_migrator.auth.manager import SpotifyAuthManager

        config = SpotifyAppConfig(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8080",
        )
        auth = SpotifyAuthManager("source", config)

        callback = "http://localhost:8080/?error=access_denied"

        with pytest.raises(AuthorizationError):
            auth._parse_callback_url(callback)

    def test_parse_code_only(self):
        """Test parsing a code only (without URL)."""
        from spotify_migrator.auth.manager import SpotifyAuthManager

        config = SpotifyAppConfig(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8080",
        )
        auth = SpotifyAuthManager("source", config)

        code = "4/abc123def456ghi789jkl"
        result = auth._parse_callback_url(code)

        assert result == "abc123def456ghi789jkl"

    def test_parse_callback_url_strips_whitespace(self):
        """Test that callback URL is stripped of whitespace."""
        from spotify_migrator.auth.manager import SpotifyAuthManager

        config = SpotifyAppConfig(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8080",
        )
        auth = SpotifyAuthManager("source", config)

        callback = "  http://localhost:8080/?code=abc123  "
        result = auth._parse_callback_url(callback)

        assert result == "abc123"

    def test_parse_empty_input_returns_none(self):
        """Test that empty input returns None."""
        from spotify_migrator.auth.manager import SpotifyAuthManager

        config = SpotifyAppConfig(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8080",
        )
        auth = SpotifyAuthManager("source", config)

        result = auth._parse_callback_url("")
        assert result is None

        result = auth._parse_callback_url("   ")
        assert result is None


class TestAuthState:
    """Tests for AuthState."""

    def test_auth_state_default(self):
        """Test AuthState default values."""
        state = AuthState(account="source")

        assert state.account == "source"
        assert state.is_authenticated is False
        assert state.user_id is None
        assert state.display_name is None
        assert state.token_expires_at is None
        assert state.needs_refresh is False

    def test_auth_state_authenticated(self, auth_state_authenticated):
        """Test AuthState with authenticated state."""
        assert auth_state_authenticated.is_authenticated is True
        assert auth_state_authenticated.user_id == "user_123"
        assert auth_state_authenticated.display_name == "Test User"
        assert auth_state_authenticated.needs_refresh is False

    def test_auth_state_expired(self, auth_state_expired):
        """Test AuthState with expired token."""
        assert auth_state_expired.is_authenticated is True
        assert auth_state_expired.needs_refresh is True
