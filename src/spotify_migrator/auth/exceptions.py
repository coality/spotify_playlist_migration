"""Auth exceptions."""


class AuthError(Exception):
    """Base authentication error."""

    def __init__(self, message: str, account: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.account = account


class TokenExpiredError(AuthError):
    """Raised when the access token has expired."""

    def __init__(self, account: str) -> None:
        super().__init__(f"Access token expired for {account} account", account=account)


class InvalidTokenError(AuthError):
    """Raised when token is invalid."""

    def __init__(self, account: str, reason: str = "Token is invalid or malformed") -> None:
        super().__init__(f"Invalid token for {account} account: {reason}", account=account)


class AuthenticationFailedError(AuthError):
    """Raised when authentication fails."""

    def __init__(self, account: str, reason: str = "Authentication failed") -> None:
        super().__init__(f"Authentication failed for {account} account: {reason}", account=account)


class AuthorizationError(AuthError):
    """Raised when user denies authorization."""

    def __init__(self, account: str) -> None:
        super().__init__(f"Authorization denied by user for {account} account", account=account)
