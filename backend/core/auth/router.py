from typing import Annotated, Optional

from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    Header,
    HTTPException,
    Request,
    Response,
    status,
)
from loguru import logger
from pydantic import BaseModel

from core.auth.dependencies import (
    get_current_user_id,
    get_jwt_token_manager,
    get_refresh_token_manager,
    get_session_manager,
    get_user_manager,
)
from core.auth.managers import RefreshTokenManager, UserManager
from core.common import AliasedBaseModel

from .config import (
    REFRESH_TOKEN_COOKIE_HTTPONLY,
    REFRESH_TOKEN_COOKIE_NAME,
    REFRESH_TOKEN_COOKIE_PATH,
    REFRESH_TOKEN_COOKIE_SAMESITE,
    REFRESH_TOKEN_COOKIE_SECURE,
    REFRESH_TOKEN_TTL_SECONDS,
)
from .exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from .managers import JWTTokenManager, SessionManager
from .schemas.user import UserResponse, UserSchemaCreate, UserSchemaSignin

logger = logger.bind(name=__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginResponse(AliasedBaseModel):
    user: UserResponse
    access_token: str


# this needs to be the BaseModel and not AliasedBaseModel
# because FastAPI's automated header extraction fails with aliasing
class SessionHeaders(BaseModel):
    host: str
    x_forwarded_for: str | None = None
    user_agent: str | None = None
    x_real_ip: str | None = None


@router.post("/signin", response_model=LoginResponse)
async def signin(
    response: Response,
    request: Request,
    credentials: UserSchemaSignin,
    user_manager: Annotated[UserManager, Depends(get_user_manager)],
    jwt_manager: Annotated[JWTTokenManager, Depends(get_jwt_token_manager)],
    session_manager: Annotated[SessionManager, Depends(get_session_manager)],
    refresh_token_manager: Annotated[
        RefreshTokenManager, Depends(get_refresh_token_manager)
    ],
    session_headers: Annotated[SessionHeaders, Header()],
) -> LoginResponse:
    try:
        user = await user_manager.authenticate_user(credentials=credentials)
        user_response = UserResponse.model_validate(
            user
        )  # have to do it here before the object goes out of sync, a sqlachemy eccentricity

        access_token = jwt_manager.create_access_token(str(user.id))

        # extract ip and user-agent
        ip = (
            session_headers.x_forwarded_for
            or session_headers.x_real_ip
            or session_headers.host
        )
        user_agent = session_headers.user_agent

        # find existing session
        session = await session_manager.find_best_matching_session(
            user_id=user.id, ip=ip, user_agent=user_agent
        )

        # create new refresh token
        new_refresh_token = refresh_token_manager.create_refresh_token()

        # refresh or create session
        if session:
            await session_manager.refresh_session(
                session=session, new_refresh_token=new_refresh_token
            )
        else:
            await session_manager.create_session(
                user_id=user.id,
                refresh_token=new_refresh_token,
                user_agent=user_agent,
                ip=ip,
            )

        # set refresh token cookie
        response.set_cookie(
            value=new_refresh_token,
            key=REFRESH_TOKEN_COOKIE_NAME,
            httponly=REFRESH_TOKEN_COOKIE_HTTPONLY,
            secure=REFRESH_TOKEN_COOKIE_SECURE,
            samesite=REFRESH_TOKEN_COOKIE_SAMESITE,
            max_age=REFRESH_TOKEN_TTL_SECONDS,
            path=REFRESH_TOKEN_COOKIE_PATH,
        )

        return LoginResponse(user=user_response, access_token=access_token)

    except (UserNotFoundError, InvalidCredentialsError):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    except Exception as e:
        logger.error(f"Error signing in user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")


@router.post("/signup", response_model=LoginResponse)
async def signup(
    response: Response,
    request: Request,
    credentials: UserSchemaCreate,
    user_manager: Annotated[UserManager, Depends(get_user_manager)],
    session_manager: Annotated[SessionManager, Depends(get_session_manager)],
    jwt_manager: Annotated[JWTTokenManager, Depends(get_jwt_token_manager)],
    refresh_token_manager: Annotated[
        RefreshTokenManager, Depends(get_refresh_token_manager)
    ],
    session_headers: Annotated[SessionHeaders, Header()],
) -> LoginResponse:
    try:
        # create user
        user = await user_manager.create_user(credentials=credentials, request=request)
        user_response = UserResponse.model_validate(user)

        # create tokens
        access_token = jwt_manager.create_access_token(user.id)
        refresh_token = refresh_token_manager.create_refresh_token()

        # extract ip and user-agent
        ip = (
            session_headers.x_forwarded_for
            or session_headers.x_real_ip
            or session_headers.host
        )
        user_agent = session_headers.user_agent
        logger.info(f"Session headers: {session_headers.model_dump_json()}")

        # create session
        await session_manager.create_session(
            user_id=user.id,
            refresh_token=refresh_token,
            user_agent=user_agent,
            ip=ip,
        )

        # set refresh token cookie
        response.set_cookie(
            value=refresh_token,
            key=REFRESH_TOKEN_COOKIE_NAME,
            httponly=REFRESH_TOKEN_COOKIE_HTTPONLY,
            secure=REFRESH_TOKEN_COOKIE_SECURE,
            samesite=REFRESH_TOKEN_COOKIE_SAMESITE,
            max_age=REFRESH_TOKEN_TTL_SECONDS,
            path=REFRESH_TOKEN_COOKIE_PATH,
        )

        return LoginResponse(user=user_response, access_token=access_token)

    except UserAlreadyExistsError as e:
        logger.error(f"User already exists: {e}")
        raise HTTPException(status_code=400, detail="User already exists.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")


@router.post("/refresh")
async def refresh(
    session_manager: Annotated[SessionManager, Depends(get_session_manager)],
    user_manager: Annotated[UserManager, Depends(get_user_manager)],
    jwt_manager: Annotated[JWTTokenManager, Depends(get_jwt_token_manager)],
    refresh_token: Annotated[
        Optional[str], Cookie(alias=REFRESH_TOKEN_COOKIE_NAME)
    ] = None,
) -> LoginResponse:
    """
    Refresh an access token using the refresh token.

    Returns new access token in the response body.
    """
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )

    # find session by refresh token
    session = await session_manager.find_session_by_refresh_token(refresh_token)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    # Validate session
    if not await session_manager.session_is_valid(session=session):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or revoked",
        )

    # get user
    user = await user_manager.find_user_by_id(user_id=session.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    # create new access token
    new_access_token = jwt_manager.create_access_token(user_id=user.id)

    return LoginResponse(
        user=UserResponse.model_validate(user), access_token=new_access_token
    )


@router.get("/me")
async def me(
    user_id: Annotated[str, Depends(get_current_user_id)],
    user_manager: Annotated[UserManager, Depends(get_user_manager)],
) -> UserResponse:
    """
    Get the current authenticated user's information.

    Requires a valid access token in the Authorization header.
    """
    user = await user_manager.find_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse.model_validate(user)
