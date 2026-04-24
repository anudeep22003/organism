from core.auth.security import (
    FernetTokenEncryptor,
    TokenDecryptionError,
)
from core.config import settings


def test_fernet_token_encryptor_round_trips_plaintext() -> None:
    encryptor = FernetTokenEncryptor(settings.fernet_encryption_key)

    ciphertext = encryptor.encrypt("google-access-token")

    assert ciphertext != "google-access-token"
    assert encryptor.decrypt(ciphertext) == "google-access-token"


def test_fernet_token_encryptor_rejects_plaintext_as_ciphertext() -> None:
    encryptor = FernetTokenEncryptor(settings.fernet_encryption_key)

    try:
        encryptor.decrypt("not-encrypted")
    except TokenDecryptionError:
        pass
    else:
        assert False, "Expected TokenDecryptionError for plaintext input"
