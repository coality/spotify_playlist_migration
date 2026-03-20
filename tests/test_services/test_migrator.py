"""Tests for PlaylistMigrator service."""

import pytest
from unittest.mock import MagicMock, patch

from spotify_migrator.services import PlaylistMigrator, chunk_list
from spotify_migrator.api import SpotifyAPIClient, PlaylistNotFoundError
from spotify_migrator.models import Playlist, PlaylistVisibility, Track, MigrationStatus


class TestPlaylistMigrator:
    """Tests for PlaylistMigrator."""

    def test_init_sets_attributes(self, mock_spotify_client):
        """Test __init__ sets correct attributes."""
        source = SpotifyAPIClient(mock_spotify_client)
        target = SpotifyAPIClient(mock_spotify_client)

        migrator = PlaylistMigrator(source, target, skip_existing=True)

        assert migrator.source == source
        assert migrator.target == target
        assert migrator.skip_existing is True

    def test_list_source_playlists(self, mock_spotify_client):
        """Test listing source playlists."""
        mock_spotify_client.current_user_playlists.return_value = {
            "items": [
                {"id": "p1", "name": "Playlist 1", "owner": {"id": "u1"}, "tracks": {"total": 5}},
            ],
            "next": None,
        }

        source = SpotifyAPIClient(mock_spotify_client)
        target = SpotifyAPIClient(mock_spotify_client)
        migrator = PlaylistMigrator(source, target)

        playlists = migrator.list_source_playlists()

        assert len(playlists) == 1
        assert playlists[0].name == "Playlist 1"

    def test_find_source_playlist_by_id(self, mock_spotify_client):
        """Test finding playlist by ID."""
        mock_spotify_client.playlist.return_value = {
            "id": "p1",
            "name": "Playlist 1",
            "owner": {"id": "u1"},
            "public": True,
            "tracks": {"total": 5},
        }

        source = SpotifyAPIClient(mock_spotify_client)
        target = SpotifyAPIClient(mock_spotify_client)
        migrator = PlaylistMigrator(source, target)

        playlist = migrator.find_source_playlist("p1", by_id=True)

        assert playlist is not None
        assert playlist.id == "p1"

    def test_find_source_playlist_by_name(self, mock_spotify_client):
        """Test finding playlist by name."""
        mock_spotify_client.current_user_playlists.return_value = {
            "items": [
                {"id": "p1", "name": "Playlist 1", "owner": {"id": "u1"}, "tracks": {"total": 5}},
            ],
            "next": None,
        }

        source = SpotifyAPIClient(mock_spotify_client)
        target = SpotifyAPIClient(mock_spotify_client)
        migrator = PlaylistMigrator(source, target)

        playlist = migrator.find_source_playlist("Playlist 1", by_id=False)

        assert playlist is not None
        assert playlist.name == "Playlist 1"

    def test_migrate_playlist_empty(self, mock_spotify_client):
        """Test migrating an empty playlist."""
        mock_spotify_client.playlist_tracks.return_value = {"items": [], "total": 0, "next": None}

        source = SpotifyAPIClient(mock_spotify_client)
        target = SpotifyAPIClient(mock_spotify_client)
        migrator = PlaylistMigrator(source, target)

        empty_playlist = Playlist(
            id="empty",
            name="Empty Playlist",
            owner_id="user",
            tracks_count=0,
        )

        result = migrator.migrate_playlist(empty_playlist)

        assert result.status == MigrationStatus.SKIPPED
        assert "Empty playlist" in result.error_message

    def test_migrate_playlist_dry_run(self, mock_spotify_client):
        """Test dry run mode doesn't make changes."""
        mock_spotify_client.playlist_tracks.return_value = {
            "items": [
                {
                    "track": {
                        "id": "track_1",
                        "name": "Track 1",
                        "artists": [{"name": "Artist"}],
                        "uri": "spotify:track:track_1",
                        "duration_ms": 180000,
                    }
                }
            ],
            "total": 1,
            "next": None,
        }

        mock_spotify_client.playlist.return_value = {
            "id": "p1",
            "name": "Playlist 1",
            "owner": {"id": "user_123"},
            "public": True,
            "tracks": {"total": 1},
        }

        source = SpotifyAPIClient(mock_spotify_client)
        target = SpotifyAPIClient(mock_spotify_client)
        migrator = PlaylistMigrator(source, target)

        playlist = Playlist(id="p1", name="Playlist 1", owner_id="user", tracks_count=1)
        result = migrator.migrate_playlist(playlist, dry_run=True)

        assert result.status == MigrationStatus.COMPLETED
        mock_spotify_client.user_playlist_create.assert_not_called()

    def test_migrate_by_name_not_found(self, mock_spotify_client):
        """Test migrate by name when playlist not found."""
        mock_spotify_client.current_user_playlists.return_value = {"items": [], "next": None}

        source = SpotifyAPIClient(mock_spotify_client)
        target = SpotifyAPIClient(mock_spotify_client)
        migrator = PlaylistMigrator(source, target)

        result = migrator.migrate_by_name("Nonexistent Playlist")

        assert result.status == MigrationStatus.FAILED
        assert "not found" in result.error_message.lower()

    def test_migrate_by_id_not_found(self, mock_spotify_client):
        """Test migrate by ID when playlist not found."""
        mock_spotify_client.playlist.side_effect = PlaylistNotFoundError("nonexistent")

        source = SpotifyAPIClient(mock_spotify_client)
        target = SpotifyAPIClient(mock_spotify_client)
        migrator = PlaylistMigrator(source, target)

        result = migrator.migrate_by_id("nonexistent_id")

        assert result.status == MigrationStatus.FAILED


class TestChunkList:
    """Tests for chunk_list utility."""

    def test_chunk_list_evenly_divisible(self):
        """Test chunking a list that divides evenly."""
        items = [1, 2, 3, 4, 5, 6]
        chunks = chunk_list(items, 2)

        assert len(chunks) == 3
        assert chunks[0] == [1, 2]
        assert chunks[1] == [3, 4]
        assert chunks[2] == [5, 6]

    def test_chunk_list_uneven(self):
        """Test chunking a list that doesn't divide evenly."""
        items = [1, 2, 3, 4, 5]
        chunks = chunk_list(items, 2)

        assert len(chunks) == 3
        assert chunks[0] == [1, 2]
        assert chunks[1] == [3, 4]
        assert chunks[2] == [5]

    def test_chunk_list_larger_than_list(self):
        """Test chunking with chunk size larger than list."""
        items = [1, 2, 3]
        chunks = chunk_list(items, 10)

        assert len(chunks) == 1
        assert chunks[0] == [1, 2, 3]

    def test_chunk_list_empty(self):
        """Test chunking an empty list."""
        items = []
        chunks = chunk_list(items, 2)

        assert len(chunks) == 0

    def test_chunk_list_single_item(self):
        """Test chunking a single item list."""
        items = [1]
        chunks = chunk_list(items, 2)

        assert len(chunks) == 1
        assert chunks[0] == [1]
