"""Track model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Track:
    """Represents a Spotify track."""

    id: str
    name: str
    artist: str
    album: str | None = None
    uri: str | None = None
    duration_ms: int | None = None
    is_available: bool = True

    @classmethod
    def from_spotify_response(cls, data: dict[str, Any]) -> Track:
        """Create a Track from Spotify API response."""
        track_id = data.get("id", "")
        name = data.get("name", "Unknown")

        artists = data.get("artists", [])
        artist = artists[0].get("name", "Unknown") if artists else "Unknown"

        album = data.get("album", {}).get("name") if data.get("album") else None
        uri = data.get("uri")
        duration_ms = data.get("duration_ms")

        is_local = data.get("is_local", False)
        is_available = not is_local and bool(uri)

        return cls(
            id=track_id,
            name=name,
            artist=artist,
            album=album,
            uri=uri,
            duration_ms=duration_ms,
            is_available=is_available,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert track to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "artist": self.artist,
            "album": self.album,
            "uri": self.uri,
            "duration_ms": self.duration_ms,
            "is_available": self.is_available,
        }

    def __str__(self) -> str:
        """String representation."""
        return f"{self.name} - {self.artist}"
