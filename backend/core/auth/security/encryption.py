from typing import Protocol

from cryptography.fernet import Fernet, InvalidToken

from core.config import settings


class TokenDecryptionError(ValueError):
    pass


class TokenEncryptor(Protocol):
    def encrypt(self, plaintext: str) -> str: ...

    def decrypt(self, ciphertext: str) -> str: ...


class LocalOnlyNonEncryptor:
    def encrypt(self, plaintext: str) -> str:
        return plaintext

    def decrypt(self, ciphertext: str) -> str:
        return ciphertext


class FernetTokenEncryptor:
    def __init__(self, key: str) -> None:
        self._fernet = Fernet(key.encode("utf-8"))

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        try:
            return self._fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise TokenDecryptionError from exc


def get_encryptor() -> TokenEncryptor:
    if settings.env == "production":
        return FernetTokenEncryptor(settings.fernet_encryption_key)
    return LocalOnlyNonEncryptor()
