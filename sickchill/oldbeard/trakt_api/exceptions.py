class traktException(Exception):
    """Base exception for all Trakt API errors."""


class traktAuthException(traktException):
    """Raised when Trakt returns an authentication/authorization error (401, invalid_grant, etc.)."""


class traktServerBusy(traktException):
    """Raised when Trakt is temporarily unavailable (5xx)."""


class traktTokenExpiredException(traktAuthException):
    """Raised when the stored refresh token is no longer valid and the user must re-authorize.

    This typically corresponds to Trakt's ``invalid_grant`` / ``session not found`` response,
    which happens for refresh tokens issued before Trakt's authentication migration or after
    a refresh token has already been consumed (refresh tokens are single-use).
    """


class traktRateLimitException(traktException):
    """Raised when Trakt returns 429 Too Many Requests."""


class traktDeviceCodePendingException(traktException):
    """Raised while polling the device code endpoint and the user has not yet approved."""


class traktDeviceCodeExpiredException(traktException):
    """Raised when the device code has expired and the user must restart authorization."""
