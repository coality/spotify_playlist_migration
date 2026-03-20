"""Tests for Track model."""

import pytest

from spotify_migrator.models.track import Track


class TestTrack:
    """Tests for Track model."""

    def test_from_spotify_response_complete(self):
        """Test creating Track from complete Spotify response."""
        data = {
            "id": "track_123",
            "name": "Test Track",
            "artists": [{"name": "Test Artist"}],
            "album": {"name": "Test Album"},
            "uri": "spotify:track:track_123",
            "duration_ms": 180000,
            "is_local": False,
        }

        track = Track.from_spotify_response(data)

        assert track.id == "track_123"
        assert track.name == "Test Track"
        assert track.artist == "Test Artist"
        assert track.album == "Test Album"
        assert track.uri == "spotify:track:track_123"
        assert track.duration_ms == 180000
        assert track.is_available is True

    def test_from_spotify_response_minimal(self):
        """Test creating Track from minimal Spotify response."""
        data = {"id": "track_123", "name": "Test Track", "artists": [], "is_local": False}

        track = Track.from_spotify_response(data)

        assert track.id == "track_123"
        assert track.name == "Test Track"
        assert track.artist == "Unknown"
        assert track.album is None
        assert track.uri is None
        assert track.is_available is False

    def test_from_spotify_response_local_track(self):
        """Test that local tracks are marked as unavailable."""
        data = {
            "id": "local_track",
            "name": "Local Track",
            "artists": [{"name": "Artist"}],
            "is_local": True,
        }

        track = Track.from_spotify_response(data)

        assert track.is_available is False

    def test_from_spotify_response_no_uri(self):
        """Test that tracks without URI are marked as unavailable."""
        data = {
            "id": "track_no_uri",
            "name": "Track No URI",
            "artists": [],
            "is_local": False,
        }

        track = Track.from_spotify_response(data)

        assert track.is_available is False

    def test_to_dict(self):
        """Test Track.to_dict()."""
        track = Track(
            id="track_123",
            name="Test Track",
            artist="Test Artist",
            album="Test Album",
            uri="spotify:track:track_123",
            duration_ms=180000,
            is_available=True,
        )

        result = track.to_dict()

        assert result["id"] == "track_123"
        assert result["name"] == "Test Track"
        assert result["artist"] == "Test Artist"
        assert result["album"] == "Test Album"

    def test_str(self):
        """Test Track string representation."""
        track = Track(
            id="track_123",
            name="Test Track",
            artist="Test Artist",
        )

        assert str(track) == "Test Track - Test Artist"
