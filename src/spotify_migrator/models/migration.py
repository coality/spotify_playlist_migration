"""Migration models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MigrationStatus(str, Enum):
    """Status of a migration operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class MigrationResult:
    """Result of a single playlist migration."""

    playlist_name: str
    playlist_id: str | None
    source_playlist_id: str
    tracks_copied: int = 0
    tracks_skipped: int = 0
    tracks_not_found: int = 0
    status: MigrationStatus = MigrationStatus.PENDING
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @property
    def is_success(self) -> bool:
        """Check if migration was successful."""
        return self.status == MigrationStatus.COMPLETED

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "playlist_name": self.playlist_name,
            "playlist_id": self.playlist_id,
            "source_playlist_id": self.source_playlist_id,
            "tracks_copied": self.tracks_copied,
            "tracks_skipped": self.tracks_skipped,
            "tracks_not_found": self.tracks_not_found,
            "status": self.status.value,
            "error_message": self.error_message,
        }


@dataclass
class MigrationSummary:
    """Summary of a complete migration operation."""

    results: list[MigrationResult] = field(default_factory=list)
    total_playlists_copied: int = 0
    total_playlists_skipped: int = 0
    total_playlists_failed: int = 0
    total_tracks_copied: int = 0
    total_tracks_not_found: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def add_result(self, result: MigrationResult) -> None:
        """Add a migration result and update counters."""
        self.results.append(result)

        if result.status == MigrationStatus.COMPLETED:
            self.total_playlists_copied += 1
            self.total_tracks_copied += result.tracks_copied
            self.total_tracks_not_found += result.tracks_not_found
        elif result.status == MigrationStatus.SKIPPED:
            self.total_playlists_skipped += 1
        elif result.status == MigrationStatus.FAILED:
            self.total_playlists_failed += 1

    @property
    def total_playlists(self) -> int:
        """Total number of playlists processed."""
        return len(self.results)

    def get_completed(self) -> list[MigrationResult]:
        """Get list of completed migrations."""
        return [r for r in self.results if r.status == MigrationStatus.COMPLETED]

    def get_skipped(self) -> list[MigrationResult]:
        """Get list of skipped migrations."""
        return [r for r in self.results if r.status == MigrationStatus.SKIPPED]

    def get_failed(self) -> list[MigrationResult]:
        """Get list of failed migrations."""
        return [r for r in self.results if r.status == MigrationStatus.FAILED]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_playlists": self.total_playlists,
            "total_playlists_copied": self.total_playlists_copied,
            "total_playlists_skipped": self.total_playlists_skipped,
            "total_playlists_failed": self.total_playlists_failed,
            "total_tracks_copied": self.total_tracks_copied,
            "total_tracks_not_found": self.total_tracks_not_found,
            "results": [r.to_dict() for r in self.results],
        }
