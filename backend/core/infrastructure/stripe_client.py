from functools import lru_cache

from stripe import HTTPXClient, StripeClient

from core.config import settings

http_client = HTTPXClient()


@lru_cache(maxsize=1)
def get_stripe_client() -> "StripeClient":
    """Return the Stripe client — once, on first call.

    @lru_cache(maxsize=1) means this function body executes exactly once regardless
    of how many times it is called. The same stripe_client is returned on every
    subsequent call with no re-instantiation.

    passing httpx as the client to force async usage
    otherwise both sync and async usage are allowed
    """
    return StripeClient(settings.stripe_secret_key, http_client=http_client)
