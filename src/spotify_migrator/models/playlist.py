"""Playlist model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from spotify_migrator.models.track import Track


class PlaylistVisibility(str, Enum):
    """Playlist visibility on Spotify."""

    PUBLIC = "public"
    PRIVATE = "private"
    UNKNOWN = "unknown"


@dataclass
class Playlist:
    """Represents a Spotify playlist."""

    id: str
    name: str
    description: str | None = None
    owner_id: str | None = None
    visibility: PlaylistVisibility = PlaylistVisibility.UNKNOWN
    tracks_count: int = 0
    tracks: list[Track] = field(default_factory=list)
    snapshot_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_spotify_response(cls, data: dict[str, Any]) -> Playlist:
        """Create a Playlist from Spotify API response."""
        playlist_id = data.get("id", "")
        name = data.get("name", "Unknown")
        description = data.get("description")
        owner_id = data.get("owner", {}).get("id")

        public_val = data.get("public")
        if public_val is True:
            visibility = PlaylistVisibility.PUBLIC
        elif public_val is False:
            visibility = PlaylistVisibility.PRIVATE
        else:
            visibility = PlaylistVisibility.UNKNOWN

        tracks_data = data.get("tracks", {})
        if isinstance(tracks_data, dict):
            tracks_count = tracks_data.get("total", 0)
        else:
            tracks_count = 0

        snapshot_id = data.get("snapshot_id")

        created_at_str = data.get("created_at")
        created_at = None
        if created_at_str:
            try:
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        updated_at_str = data.get("updated_at")
        updated_at = None
        if updated_at_str:
            try:
                updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        return cls(
            id=playlist_id,
            name=name,
            description=description,
            owner_id=owner_id,
            visibility=visibility,
            tracks_count=tracks_count,
            snapshot_id=snapshot_id,
            created_at=created_at,
            updated_at=updated_at,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert playlist to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "visibility": self.visibility.value,
            "tracks_count": self.tracks_count,
            "tracks": [t.to_dict() for t in self.tracks],
            "snapshot_id": self.snapshot_id,
        }

    def __str__(self) -> str:
        """String representation."""
        return f"{self.name} ({self.tracks_count} tracks)"
