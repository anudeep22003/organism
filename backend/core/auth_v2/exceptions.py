class AuthV2Error(Exception):
    pass


class OAuthError(AuthV2Error):
    pass


class OAuthTokenExchangeError(OAuthError):
    pass


class OAuthUserInfoError(OAuthError):
    pass


class OAuthProfileFieldError(OAuthError):
    pass


class RateLimitExceededError(AuthV2Error):
    def __init__(self, retry_after: int | None = None) -> None:
        super().__init__("Too many requests")
        self.retry_after = retry_after


class InvalidAccessTokenError(AuthV2Error):
    pass


class ExpiredAccessTokenError(AuthV2Error):
    pass


class InvalidRefreshTokenError(AuthV2Error):
    pass


class UserNotFoundError(AuthV2Error):
    pass
