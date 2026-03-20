"""Migration service for copying playlists."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from spotify_migrator.api import SpotifyAPIClient, PlaylistNotFoundError, TrackNotFoundError
from spotify_migrator.models.migration import MigrationResult, MigrationStatus, MigrationSummary
from spotify_migrator.models.playlist import Playlist, PlaylistVisibility
from spotify_migrator.models.track import Track

logger = logging.getLogger(__name__)


@dataclass
class MigrationProgress:
    """Progress callback data."""

    playlist_name: str
    current_track: int
    total_tracks: int
    track_name: str
    status: str


class PlaylistMigrator:
    """Handles the migration of playlists between Spotify accounts."""

    def __init__(
        self,
        source_client: SpotifyAPIClient,
        target_client: SpotifyAPIClient,
        skip_existing: bool = False,
        default_visibility: PlaylistVisibility | None = None,
    ) -> None:
        self.source = source_client
        self.target = target_client
        self.skip_existing = skip_existing
        self.default_visibility = default_visibility

    def list_source_playlists(self) -> list[Playlist]:
        """List all playlists from source account."""
        logger.info("Fetching source playlists...")
        playlists = list(self.source.get_user_playlists())
        logger.info(f"Found {len(playlists)} playlists on source account")
        return playlists

    def find_source_playlist(self, identifier: str, by_id: bool = False) -> Playlist | None:
        """Find a source playlist by name or ID."""
        if by_id:
            try:
                return self.source.get_playlist(identifier)
            except PlaylistNotFoundError:
                return None
        else:
            return self.source.find_playlist_by_name(identifier)

    def _load_playlist_tracks(self, playlist: Playlist) -> list[Track]:
        """Load all tracks from a playlist."""
        logger.debug(f"Loading tracks for playlist: {playlist.name}")
        tracks = list(self.source.get_playlist_tracks(playlist.id))
        playlist.tracks = tracks
        playlist.tracks_count = len(tracks)
        logger.debug(f"Loaded {len(tracks)} tracks from {playlist.name}")
        return tracks

    def _create_or_find_target_playlist(
        self,
        source_playlist: Playlist,
        dry_run: bool = False,
    ) -> tuple[Playlist | None, bool]:
        """Create playlist on target or find existing one."""
        existing = self.target.find_playlist_by_name(source_playlist.name)

        if existing:
            if self.skip_existing:
                logger.info(f"Playlist '{source_playlist.name}' already exists on target, skipping")
                return existing, True
            else:
                logger.warning(f"Playlist '{source_playlist.name}' already exists on target")
                name_suffix = f" ({datetime.now().strftime('%Y%m%d_%H%M%S')})"
                new_name = source_playlist.name + name_suffix
                logger.info(f"Creating with modified name: {new_name}")
                return self._create_playlist(source_playlist, new_name, dry_run), False

        return self._create_playlist(source_playlist, source_playlist.name, dry_run), False

    def _create_playlist(
        self,
        source_playlist: Playlist,
        name: str,
        dry_run: bool = False,
    ) -> Playlist | None:
        """Create a new playlist on target account."""
        if dry_run:
            logger.info(f"[DRY RUN] Would create playlist: {name}")
            return None

        visibility = self._determine_visibility(source_playlist)
        playlist = self.target.create_playlist(
            name=name,
            description=source_playlist.description,
            public=visibility if visibility != PlaylistVisibility.UNKNOWN else None,
        )
        return playlist

    def _determine_visibility(self, playlist: Playlist) -> PlaylistVisibility:
        """Determine playlist visibility."""
        if self.default_visibility:
            return self.default_visibility
        return playlist.visibility

    def _get_track_uris(self, tracks: list[Track]) -> tuple[list[str], int]:
        """Extract URIs from tracks, filtering unavailable ones. Returns (uris, not_found_count)."""
        uris = []
        not_found_count = 0

        for track in tracks:
            if track.uri and track.is_available:
                uris.append(track.uri)
            else:
                logger.debug(f"Skipping unavailable track: {track.name} ({track.id})")
                not_found_count += 1

        return uris, not_found_count

    def _deduplicate_tracks(self, tracks: list[Track]) -> tuple[list[Track], int]:
        """Remove duplicate tracks based on URI. Returns (unique_tracks, duplicate_count)."""
        seen_uris: set[str] = set()
        unique_tracks: list[Track] = []
        duplicate_count = 0

        for track in tracks:
            if track.uri and track.uri not in seen_uris:
                seen_uris.add(track.uri)
                unique_tracks.append(track)
            elif not track.uri:
                unique_tracks.append(track)
            else:
                duplicate_count += 1

        if duplicate_count > 0:
            logger.debug(f"Removed {duplicate_count} duplicate tracks")

        return unique_tracks, duplicate_count

    def migrate_playlist(
        self,
        source_playlist: Playlist,
        dry_run: bool = False,
        progress_callback: Callable[[MigrationProgress], None] | None = None,
    ) -> MigrationResult:
        """Migrate a single playlist to target account."""
        result = MigrationResult(
            playlist_name=source_playlist.name,
            playlist_id=None,
            source_playlist_id=source_playlist.id,
            status=MigrationStatus.IN_PROGRESS,
            started_at=datetime.now(),
        )

        try:
            logger.info(f"Migrating playlist: {source_playlist.name}")

            tracks = self._load_playlist_tracks(source_playlist)
            original_count = len(tracks)

            if original_count == 0:
                logger.warning(f"Playlist '{source_playlist.name}' is empty, skipping")
                result.status = MigrationStatus.SKIPPED
                result.error_message = "Empty playlist"
                result.completed_at = datetime.now()
                return result

            tracks, dup_count = self._deduplicate_tracks(tracks)
            result.tracks_skipped = dup_count

            target_playlist, skipped = self._create_or_find_target_playlist(source_playlist, dry_run)

            if skipped:
                result.status = MigrationStatus.SKIPPED
                result.error_message = "Playlist already exists"
                result.completed_at = datetime.now()
                return result

            if dry_run:
                result.status = MigrationStatus.COMPLETED
                result.tracks_copied = len(tracks)
                result.completed_at = datetime.now()
                return result

            if not target_playlist:
                result.status = MigrationStatus.FAILED
                result.error_message = "Failed to create playlist"
                result.completed_at = datetime.now()
                return result

            result.playlist_id = target_playlist.id

            uris, not_found_count = self._get_track_uris(tracks)
            result.tracks_not_found = not_found_count

            for i, track in enumerate(tracks):
                if progress_callback:
                    progress_callback(MigrationProgress(
                        playlist_name=source_playlist.name,
                        current_track=i + 1,
                        total_tracks=len(tracks),
                        track_name=track.name,
                        status="copying",
                    ))

            success_count, failed_count, failed_uris = self.target.add_tracks_to_playlist(
                target_playlist.id, uris
            )

            result.tracks_copied = success_count
            result.tracks_not_found += failed_count

            result.status = MigrationStatus.COMPLETED
            result.completed_at = datetime.now()

            logger.info(
                f"Successfully migrated '{source_playlist.name}': "
                f"{result.tracks_copied} tracks copied, "
                f"{result.tracks_not_found} not found"
            )

        except PlaylistNotFoundError as e:
            result.status = MigrationStatus.FAILED
            result.error_message = str(e)
            result.completed_at = datetime.now()
            logger.error(f"Playlist not found: {e}")
        except TrackNotFoundError as e:
            result.status = MigrationStatus.FAILED
            result.error_message = str(e)
            result.completed_at = datetime.now()
            logger.error(f"Track not found: {e}")
        except Exception as e:
            result.status = MigrationStatus.FAILED
            result.error_message = str(e)
            result.completed_at = datetime.now()
            logger.error(f"Migration failed for '{source_playlist.name}': {e}")

        return result

    def migrate_all(
        self,
        dry_run: bool = False,
        progress_callback: Callable[[MigrationProgress], None] | None = None,
    ) -> MigrationSummary:
        """Migrate all playlists from source to target."""
        summary = MigrationSummary(started_at=datetime.now())

        try:
            source_playlists = self.list_source_playlists()

            for playlist in source_playlists:
                result = self.migrate_playlist(playlist, dry_run=dry_run, progress_callback=progress_callback)
                summary.add_result(result)

        except Exception as e:
            logger.error(f"Migration process failed: {e}")

        summary.completed_at = datetime.now()
        return summary

    def migrate_by_name(
        self,
        playlist_name: str,
        dry_run: bool = False,
        progress_callback: Callable[[MigrationProgress], None] | None = None,
    ) -> MigrationResult:
        """Migrate a specific playlist by name."""
        playlist = self.find_source_playlist(playlist_name, by_id=False)

        if not playlist:
            result = MigrationResult(
                playlist_name=playlist_name,
                playlist_id=None,
                source_playlist_id="",
                status=MigrationStatus.FAILED,
                error_message=f"Playlist not found: {playlist_name}",
            )
            return result

        return self.migrate_playlist(playlist, dry_run=dry_run, progress_callback=progress_callback)

    def migrate_by_id(
        self,
        playlist_id: str,
        dry_run: bool = False,
        progress_callback: Callable[[MigrationProgress], None] | None = None,
    ) -> MigrationResult:
        """Migrate a specific playlist by ID."""
        try:
            playlist = self.source.get_playlist(playlist_id)
            return self.migrate_playlist(playlist, dry_run=dry_run, progress_callback=progress_callback)
        except PlaylistNotFoundError as e:
            result = MigrationResult(
                playlist_name="",
                playlist_id=None,
                source_playlist_id=playlist_id,
                status=MigrationStatus.FAILED,
                error_message=str(e),
            )
            return result
