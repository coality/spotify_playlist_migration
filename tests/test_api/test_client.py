"""Tests for SpotifyAPIClient."""

import pytest
from unittest.mock import MagicMock, patch

from spotify_migrator.api import SpotifyAPIClient, RateLimitError, PlaylistNotFoundError
from spotify_migrator.models import Playlist, PlaylistVisibility
from spotipy.exceptions import SpotifyException


class TestSpotifyAPIClient:
    """Tests for SpotifyAPIClient."""

    def test_init_sets_attributes(self, mock_spotify_client):
        """Test __init__ sets client and configuration."""
        client = SpotifyAPIClient(mock_spotify_client, max_retries=5, retry_delay=2.0)
        assert client.sp == mock_spotify_client
        assert client.max_retries == 5
        assert client.retry_delay == 2.0

    def test_get_current_user(self, mock_spotify_client):
        """Test getting current user info."""
        mock_spotify_client.current_user.return_value = {"id": "user123", "display_name": "Test"}
        client = SpotifyAPIClient(mock_spotify_client)

        result = client.get_current_user()

        assert result["id"] == "user123"
        mock_spotify_client.current_user.assert_called_once()

    def test_get_user_playlists_pagination(self, mock_spotify_client):
        """Test pagination in get_user_playlists."""
        mock_spotify_client.current_user_playlists.side_effect = [
            {
                "items": [
                    {"id": "p1", "name": "Playlist 1", "owner": {"id": "u1"}, "tracks": {"total": 10}},
                    {"id": "p2", "name": "Playlist 2", "owner": {"id": "u1"}, "tracks": {"total": 5}},
                ],
                "next": True,
            },
            {
                "items": [{"id": "p3", "name": "Playlist 3", "owner": {"id": "u1"}, "tracks": {"total": 3}}],
                "next": None,
            },
        ]

        client = SpotifyAPIClient(mock_spotify_client)
        playlists = list(client.get_user_playlists())

        assert len(playlists) == 3
        assert playlists[0].name == "Playlist 1"
        assert playlists[1].name == "Playlist 2"
        assert playlists[2].name == "Playlist 3"

    def test_get_user_playlists_empty(self, mock_spotify_client):
        """Test get_user_playlists with no playlists."""
        mock_spotify_client.current_user_playlists.return_value = {"items": [], "next": None}

        client = SpotifyAPIClient(mock_spotify_client)
        playlists = list(client.get_user_playlists())

        assert len(playlists) == 0

    def test_get_playlist(self, mock_spotify_client):
        """Test getting a specific playlist."""
        mock_spotify_client.playlist.return_value = {
            "id": "playlist_123",
            "name": "My Playlist",
            "description": "Test description",
            "owner": {"id": "user_123"},
            "public": True,
            "tracks": {"total": 10},
            "snapshot_id": "snapshot_123",
        }

        client = SpotifyAPIClient(mock_spotify_client)
        playlist = client.get_playlist("playlist_123")

        assert playlist.id == "playlist_123"
        assert playlist.name == "My Playlist"
        assert playlist.visibility == PlaylistVisibility.PUBLIC

    def test_get_playlist_not_found(self, mock_spotify_client):
        """Test getting non-existent playlist raises error."""
        mock_spotify_client.playlist.side_effect = SpotifyException(
            http_status=404, code="NOT_FOUND", msg="Playlist not found"
        )

        client = SpotifyAPIClient(mock_spotify_client)

        with pytest.raises(PlaylistNotFoundError):
            client.get_playlist("nonexistent")

    def test_get_playlist_tracks(self, mock_spotify_client):
        """Test getting playlist tracks."""
        mock_spotify_client.playlist_tracks.return_value = {
            "items": [
                {
                    "track": {
                        "id": "track_1",
                        "name": "Track 1",
                        "artists": [{"name": "Artist 1"}],
                        "album": {"name": "Album 1"},
                        "uri": "spotify:track:track_1",
                        "duration_ms": 180000,
                    }
                }
            ],
            "total": 1,
            "next": None,
        }

        client = SpotifyAPIClient(mock_spotify_client)
        tracks = list(client.get_playlist_tracks("playlist_123"))

        assert len(tracks) == 1
        assert tracks[0].id == "track_1"
        assert tracks[0].name == "Track 1"

    def test_create_playlist(self, mock_spotify_client):
        """Test creating a playlist."""
        mock_spotify_client.current_user.return_value = {"id": "user_123"}
        mock_spotify_client.user_playlist_create.return_value = {
            "id": "new_playlist_123",
            "name": "New Playlist",
            "description": "New description",
            "owner": {"id": "user_123"},
            "public": False,
            "tracks": {"total": 0},
        }

        client = SpotifyAPIClient(mock_spotify_client)
        playlist = client.create_playlist(
            name="New Playlist",
            description="New description",
            public=False,
        )

        assert playlist.id == "new_playlist_123"
        assert playlist.name == "New Playlist"

    def test_find_playlist_by_name(self, mock_spotify_client):
        """Test finding playlist by exact name."""
        mock_spotify_client.current_user_playlists.return_value = {
            "items": [
                {"id": "p1", "name": "My Playlist", "owner": {"id": "u1"}, "tracks": {"total": 5}},
            ],
            "next": None,
        }

        client = SpotifyAPIClient(mock_spotify_client)
        playlist = client.find_playlist_by_name("My Playlist")

        assert playlist is not None
        assert playlist.name == "My Playlist"

    def test_find_playlist_by_name_case_insensitive(self, mock_spotify_client):
        """Test finding playlist by name is case insensitive."""
        mock_spotify_client.current_user_playlists.return_value = {
            "items": [
                {"id": "p1", "name": "My Playlist", "owner": {"id": "u1"}, "tracks": {"total": 5}},
            ],
            "next": None,
        }

        client = SpotifyAPIClient(mock_spotify_client)
        playlist = client.find_playlist_by_name("my playlist")

        assert playlist is not None
        assert playlist.name == "My Playlist"

    def test_find_playlist_by_name_not_found(self, mock_spotify_client):
        """Test finding non-existent playlist returns None."""
        mock_spotify_client.current_user_playlists.return_value = {
            "items": [],
            "next": None,
        }

        client = SpotifyAPIClient(mock_spotify_client)
        playlist = client.find_playlist_by_name("Nonexistent")

        assert playlist is None

    def test_add_tracks_to_playlist(self, mock_spotify_client):
        """Test adding tracks to playlist."""
        mock_spotify_client.playlist_add_items.return_value = {"snapshot_id": "snapshot"}

        client = SpotifyAPIClient(mock_spotify_client, batch_size=100)
        success, failed, failed_ids = client.add_tracks_to_playlist(
            "playlist_123",
            ["spotify:track:t1", "spotify:track:t2"],
        )

        assert success == 2
        assert failed == 0
        assert failed_ids == []

    def test_rate_limit_retry(self, mock_spotify_client):
        """Test retry on rate limit."""
        mock_spotify_client.current_user.side_effect = [
            SpotifyException(http_status=429, code="RATE_LIMIT", msg="Rate limited", headers={"Retry-After": "1"}),
            {"id": "user123"},
        ]

        client = SpotifyAPIClient(mock_spotify_client, max_retries=3, retry_delay=0.1)
        result = client.get_current_user()

        assert result["id"] == "user123"
        assert mock_spotify_client.current_user.call_count == 2

    def test_max_retries_exceeded(self, mock_spotify_client):
        """Test that max retries is respected."""
        mock_spotify_client.current_user.side_effect = SpotifyException(
            http_status=429, code="RATE_LIMIT", msg="Rate limited"
        )

        client = SpotifyAPIClient(mock_spotify_client, max_retries=3, retry_delay=0.01)

        with pytest.raises(RateLimitError):
            client.get_current_user()

        assert mock_spotify_client.current_user.call_count == 3
