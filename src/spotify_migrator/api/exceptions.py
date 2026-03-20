"""API exceptions."""


class APIError(Exception):
    """Base API error."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class RateLimitError(APIError):
    """Raised when rate limited (HTTP 429)."""

    def __init__(self, retry_after: int | None = None) -> None:
        super().__init__("Rate limited by Spotify API", status_code=429)
        self.retry_after = retry_after


class NetworkError(APIError):
    """Raised for network errors."""

    def __init__(self, message: str = "Network error occurred") -> None:
        super().__init__(message)


class PlaylistNotFoundError(APIError):
    """Raised when playlist is not found."""

    def __init__(self, playlist_id: str) -> None:
        super().__init__(f"Playlist not found: {playlist_id}", status_code=404)
        self.playlist_id = playlist_id


class TrackNotFoundError(APIError):
    """Raised when track is not found or unavailable."""

    def __init__(self, track_id: str, track_name: str | None = None) -> None:
        message = f"Track not found: {track_id}"
        if track_name:
            message = f"Track not found: {track_name} ({track_id})"
        super().__init__(message, status_code=404)
        self.track_id = track_id
        self.track_name = track_name
