"""Spotify API client with retry logic and rate limiting."""

from __future__ import annotations

import logging
import time
from typing import Any, Iterator

import spotipy
from spotipy.exceptions import SpotifyException

from spotify_migrator.api.exceptions import (
    APIError,
    NetworkError,
    PlaylistNotFoundError,
    RateLimitError,
    TrackNotFoundError,
)
from spotify_migrator.models.playlist import Playlist
from spotify_migrator.models.track import Track

logger = logging.getLogger(__name__)

MAX_BATCH_SIZE = 100
DEFAULT_RETRY_DELAY = 1.0
MAX_RETRIES = 3


class SpotifyAPIClient:
    """Wrapper around spotipy with retry and rate limiting logic."""

    def __init__(
        self,
        sp: spotipy.Spotify,
        max_retries: int = MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        batch_size: int = MAX_BATCH_SIZE,
    ) -> None:
        self.sp = sp
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.batch_size = batch_size

    def _handle_spotify_exception(self, e: SpotifyException) -> None:
        """Handle Spotify exception and convert to appropriate error."""
        if e.http_status == 401:
            raise TrackNotFoundError("unknown", "Token expired")
        elif e.http_status == 403:
            raise APIError(f"Forbidden: {e}", status_code=403)
        elif e.http_status == 404:
            if "track" in str(e).lower():
                raise TrackNotFoundError("unknown", str(e))
            elif "playlist" in str(e).lower():
                raise PlaylistNotFoundError("unknown")
            raise APIError(f"Not found: {e}", status_code=404)
        elif e.http_status == 429:
            headers = getattr(e, "headers", None) if hasattr(e, "headers") else None
            retry_after = None
            if headers:
                retry_after_str = headers.get("Retry-After")
                if retry_after_str:
                    retry_after = int(retry_after_str)
            raise RateLimitError(retry_after=retry_after)
        else:
            raise APIError(f"API error: {e}", status_code=e.http_status)

    def _execute_with_retry(self, operation: str, func: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation with retry logic for rate limiting."""
        last_exception: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except RateLimitError as e:
                last_exception = e
                retry_after = e.retry_after if e.retry_after else int(self.retry_delay * (2 ** attempt))
                logger.warning(f"Rate limited. Retrying in {retry_after}s (attempt {attempt + 1}/{self.max_retries})")
                time.sleep(retry_after)
            except SpotifyException as e:
                if e.http_status == 429:
                    last_exception = RateLimitError()
                    retry_delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Rate limited. Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    self._handle_spotify_exception(e)
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)
                        logger.warning(f"Spotify error during {operation}: {e}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        raise
            except (NetworkError, APIError) as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"{operation} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    last_exception = e
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"{operation} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    last_exception = e

        if last_exception:
            raise last_exception

        raise APIError(f"Operation {operation} failed after {self.max_retries} retries")

    def get_current_user(self) -> dict[str, Any]:
        """Get current user info."""
        return self._execute_with_retry("get_current_user", self.sp.current_user)

    def get_user_playlists(self, limit: int = 50) -> Iterator[Playlist]:
        """Get all playlists for the current user with pagination."""
        offset = 0

        while True:
            response = self._execute_with_retry(
                "get_user_playlists",
                self.sp.current_user_playlists,
                limit=limit,
                offset=offset,
            )

            items = response.get("items", [])
            if not items:
                break

            for item in items:
                yield Playlist.from_spotify_response(item)

            if response.get("next"):
                offset += limit
            else:
                break

    def get_playlist(self, playlist_id: str) -> Playlist:
        """Get a specific playlist by ID."""
        try:
            response = self._execute_with_retry("get_playlist", self.sp.playlist, playlist_id)
            return Playlist.from_spotify_response(response)
        except SpotifyException as e:
            if e.http_status == 404:
                raise PlaylistNotFoundError(playlist_id) from e
            self._handle_spotify_exception(e)

    def get_playlist_tracks(self, playlist_id: str) -> Iterator[Track]:
        """Get all tracks in a playlist with pagination."""
        offset = 0

        while True:
            response = self._execute_with_retry(
                "get_playlist_tracks",
                self.sp.playlist_tracks,
                playlist_id,
                limit=self.batch_size,
                offset=offset,
                fields="items(track(id,name,artists,album,duration_ms,uri,is_local)),total,next",
            )

            items = response.get("items", [])
            if not items:
                break

            for item in items:
                track_data = item.get("track")
                if track_data and track_data.get("id"):
                    yield Track.from_spotify_response(track_data)

            if response.get("next"):
                offset += self.batch_size
            else:
                break

    def create_playlist(
        self,
        name: str,
        description: str | None = None,
        public: bool | None = None,
    ) -> Playlist:
        """Create a new playlist."""
        user = self.get_current_user()
        user_id = user.get("id")

        response = self._execute_with_retry(
            "create_playlist",
            self.sp.user_playlist_create,
            user_id,
            name,
            public=public,
            description=description or "",
        )

        logger.info(f"Created playlist: {name} (ID: {response.get('id')})")
        return Playlist.from_spotify_response(response)

    def find_playlist_by_name(self, name: str) -> Playlist | None:
        """Find a playlist by exact name (case-insensitive)."""
        for playlist in self.get_user_playlists():
            if playlist.name.lower() == name.lower():
                return playlist
        return None

    def add_tracks_to_playlist(self, playlist_id: str, track_uris: list[str]) -> tuple[int, int, list[str]]:
        """Add tracks to a playlist in batches. Returns (success_count, failed_count, failed_uris)."""
        success_count = 0
        failed_count = 0
        failed_ids: list[str] = []

        for i in range(0, len(track_uris), self.batch_size):
            batch = track_uris[i : i + self.batch_size]
            try:
                self._execute_with_retry(
                    "add_tracks",
                    self.sp.playlist_add_items,
                    playlist_id,
                    batch,
                )
                success_count += len(batch)
                logger.debug(f"Added {len(batch)} tracks to playlist {playlist_id}")
            except TrackNotFoundError as e:
                logger.warning(f"Some tracks not found: {e}")
                failed_count += len(batch)
                failed_ids.extend(batch)
            except SpotifyException as e:
                if e.http_status == 404:
                    for uri in batch:
                        failed_ids.append(uri)
                    failed_count += len(batch)
                elif e.http_status == 429:
                    raise RateLimitError() from e
                else:
                    raise APIError(f"API error during add_tracks: {e}", status_code=e.http_status) from e

        return success_count, failed_count, failed_ids
