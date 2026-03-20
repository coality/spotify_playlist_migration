"""API package."""

from spotify_migrator.api.client import SpotifyAPIClient
from spotify_migrator.api.exceptions import (
    APIError,
    RateLimitError,
    NetworkError,
    PlaylistNotFoundError,
    TrackNotFoundError,
)

__all__ = [
    "SpotifyAPIClient",
    "APIError",
    "RateLimitError",
    "NetworkError",
    "PlaylistNotFoundError",
    "TrackNotFoundError",
]
