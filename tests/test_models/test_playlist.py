"""Tests for Playlist model."""

import pytest

from spotify_migrator.models.playlist import Playlist, PlaylistVisibility


class TestPlaylist:
    """Tests for Playlist model."""

    def test_from_spotify_response_complete(self):
        """Test creating Playlist from complete Spotify response."""
        data = {
            "id": "playlist_123",
            "name": "Test Playlist",
            "description": "A test playlist",
            "owner": {"id": "user_123"},
            "public": True,
            "tracks": {"total": 10},
            "snapshot_id": "snapshot_123",
        }

        playlist = Playlist.from_spotify_response(data)

        assert playlist.id == "playlist_123"
        assert playlist.name == "Test Playlist"
        assert playlist.description == "A test playlist"
        assert playlist.owner_id == "user_123"
        assert playlist.visibility == PlaylistVisibility.PUBLIC
        assert playlist.tracks_count == 10
        assert playlist.snapshot_id == "snapshot_123"

    def test_from_spotify_response_private(self):
        """Test creating private Playlist from Spotify response."""
        data = {
            "id": "playlist_123",
            "name": "Private Playlist",
            "owner": {"id": "user_123"},
            "public": False,
            "tracks": {"total": 5},
        }

        playlist = Playlist.from_spotify_response(data)

        assert playlist.visibility == PlaylistVisibility.PRIVATE

    def test_from_spotify_response_unknown_visibility(self):
        """Test creating Playlist with unknown visibility."""
        data = {
            "id": "playlist_123",
            "name": "Playlist",
            "owner": {"id": "user_123"},
            "public": None,
            "tracks": {"total": 0},
        }

        playlist = Playlist.from_spotify_response(data)

        assert playlist.visibility == PlaylistVisibility.UNKNOWN

    def test_from_spotify_response_tracks_as_list(self):
        """Test that tracks.total is extracted correctly when tracks is a dict."""
        data = {
            "id": "playlist_123",
            "name": "Playlist",
            "owner": {"id": "user_123"},
            "tracks": {"total": 15},
        }

        playlist = Playlist.from_spotify_response(data)

        assert playlist.tracks_count == 15

    def test_to_dict(self):
        """Test Playlist.to_dict()."""
        playlist = Playlist(
            id="playlist_123",
            name="Test Playlist",
            description="Description",
            owner_id="user_123",
            visibility=PlaylistVisibility.PUBLIC,
            tracks_count=5,
        )

        result = playlist.to_dict()

        assert result["id"] == "playlist_123"
        assert result["name"] == "Test Playlist"
        assert result["visibility"] == "public"

    def test_str(self):
        """Test Playlist string representation."""
        playlist = Playlist(
            id="playlist_123",
            name="Test Playlist",
            tracks_count=10,
        )

        assert str(playlist) == "Test Playlist (10 tracks)"


class TestPlaylistVisibility:
    """Tests for PlaylistVisibility enum."""

    def test_visibility_values(self):
        """Test PlaylistVisibility enum values."""
        assert PlaylistVisibility.PUBLIC.value == "public"
        assert PlaylistVisibility.PRIVATE.value == "private"
        assert PlaylistVisibility.UNKNOWN.value == "unknown"
