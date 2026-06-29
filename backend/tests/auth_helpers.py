import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.config import ACCESS_TOKEN_COOKIE_NAME
from core.auth.security import AccessTokenManager
from core.payments.models import Entitlement

_access_token_manager = AccessTokenManager()


def auth_cookie_header(user_id: uuid.UUID | str) -> dict[str, str]:
    if isinstance(user_id, str):
        user_id = uuid.UUID(user_id)

    token = _access_token_manager.create_access_token(user_id)
    return {"cookie": f"{ACCESS_TOKEN_COOKIE_NAME}={token}"}


async def grant_pro_tier_entitlement(
    db_session: AsyncSession,
    *,
    user_id: uuid.UUID,
) -> None:
    db_session.add(
        Entitlement(
            user_id=user_id,
            feature="pro_tier",
            source="test_fixture",
            source_id=None,
            valid_from=datetime.now(timezone.utc),
            valid_until=None,
        )
    )
    await db_session.commit()
