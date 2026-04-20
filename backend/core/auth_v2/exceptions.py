class AuthV2Error(Exception):
    pass


class InvalidAccessTokenError(AuthV2Error):
    pass


class ExpiredAccessTokenError(AuthV2Error):
    pass


class InvalidRefreshTokenError(AuthV2Error):
    pass


class UserNotFoundError(AuthV2Error):
    pass
