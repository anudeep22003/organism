class AuthError(Exception):
    pass


class OAuthError(AuthError):
    pass


class OAuthTokenExchangeError(OAuthError):
    pass


class OAuthUserInfoError(OAuthError):
    pass


class OAuthProfileFieldError(OAuthError):
    pass


class RateLimitExceededError(AuthError):
    def __init__(self, retry_after: int | None = None) -> None:
        super().__init__("Too many requests")
        self.retry_after = retry_after


class InvalidAccessTokenError(AuthError):
    pass


class ExpiredAccessTokenError(AuthError):
    pass


class InvalidRefreshTokenError(AuthError):
    pass


class UserNotFoundError(AuthError):
    pass
