"""Pytest configuration and fixtures."""

import os
from unittest.mock import MagicMock, patch

import pytest

from spotify_migrator.auth import SpotifyAppConfig, AuthState
from spotify_migrator.models import Playlist, PlaylistVisibility, Track


@pytest.fixture
def mock_env_vars():
    """Set up mock environment variables."""
    env_vars = {
        "SPOTIFY_SOURCE_CLIENT_ID": "source_client_123",
        "SPOTIFY_SOURCE_CLIENT_SECRET": "source_secret_123",
        "SPOTIFY_SOURCE_REDIRECT_URI": "http://localhost:8080",
        "SPOTIFY_TARGET_CLIENT_ID": "target_client_123",
        "SPOTIFY_TARGET_CLIENT_SECRET": "target_secret_123",
        "SPOTIFY_TARGET_REDIRECT_URI": "http://localhost:8080",
        "LOG_LEVEL": "INFO",
    }
    with patch.dict(os.environ, env_vars, clear=True):
        yield env_vars


@pytest.fixture
def source_config():
    """Create a source Spotify app config."""
    return SpotifyAppConfig(
        client_id="source_client_123",
        client_secret="source_secret_123",
        redirect_uri="http://localhost:8080",
    )


@pytest.fixture
def target_config():
    """Create a target Spotify app config."""
    return SpotifyAppConfig(
        client_id="target_client_123",
        client_secret="target_secret_123",
        redirect_uri="http://localhost:8080",
    )


@pytest.fixture
def sample_track():
    """Create a sample track."""
    return Track(
        id="track_123",
        name="Test Track",
        artist="Test Artist",
        album="Test Album",
        uri="spotify:track:track_123",
        duration_ms=180000,
        is_available=True,
    )


@pytest.fixture
def sample_tracks(sample_track):
    """Create a list of sample tracks."""
    return [
        Track(
            id=f"track_{i}",
            name=f"Track {i}",
            artist="Artist",
            album="Album",
            uri=f"spotify:track:track_{i}",
            duration_ms=180000,
            is_available=True,
        )
        for i in range(5)
    ]


@pytest.fixture
def sample_playlist(sample_tracks):
    """Create a sample playlist."""
    return Playlist(
        id="playlist_123",
        name="Test Playlist",
        description="A test playlist",
        owner_id="user_123",
        visibility=PlaylistVisibility.PUBLIC,
        tracks_count=len(sample_tracks),
        tracks=sample_tracks,
    )


@pytest.fixture
def empty_playlist():
    """Create an empty playlist."""
    return Playlist(
        id="playlist_empty",
        name="Empty Playlist",
        description="",
        owner_id="user_123",
        visibility=PlaylistVisibility.PRIVATE,
        tracks_count=0,
        tracks=[],
    )


@pytest.fixture
def mock_spotify_client():
    """Create a mock Spotify client."""
    mock = MagicMock()
    mock.current_user.return_value = {"id": "test_user", "display_name": "Test User"}
    return mock


@pytest.fixture
def auth_state_authenticated():
    """Create an authenticated state."""
    import time
    return AuthState(
        account="source",
        is_authenticated=True,
        user_id="user_123",
        display_name="Test User",
        token_expires_at=time.time() + 3600,
        needs_refresh=False,
    )


@pytest.fixture
def auth_state_expired():
    """Create an expired token state."""
    import time
    return AuthState(
        account="source",
        is_authenticated=True,
        user_id="user_123",
        display_name="Test User",
        token_expires_at=time.time() - 3600,
        needs_refresh=True,
    )
