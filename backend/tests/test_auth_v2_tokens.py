import uuid

from core.auth_v2.security import Argon2Hasher, RefreshTokenManager


def test_argon2_hasher_hashes_and_verifies_secret() -> None:
    hasher = Argon2Hasher()

    hashed = hasher.hash("top-secret")

    assert hashed != "top-secret"
    assert hashed.startswith("$argon2")
    assert hasher.verify("top-secret", hashed)
    assert not hasher.verify("wrong-secret", hashed)


def test_argon2_hasher_rejects_unknown_hash_format() -> None:
    hasher = Argon2Hasher()

    assert not hasher.verify("top-secret", "plain-sha256-style-hash")


def test_refresh_token_manager_uses_argon2_for_refresh_secrets() -> None:
    manager = RefreshTokenManager(password_hasher=Argon2Hasher())

    refresh_token, refresh_token_hash = manager.create_refresh_token(uuid.uuid4())
    token_parts = manager.parse_refresh_token(refresh_token)

    assert refresh_token_hash.startswith("$argon2")
    assert manager.verify_refresh_token_secret(token_parts.secret, refresh_token_hash)
    assert not manager.verify_refresh_token_secret("wrong-secret", refresh_token_hash)
