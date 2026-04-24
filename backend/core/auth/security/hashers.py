from typing import Protocol

from passlib.context import CryptContext
from passlib.exc import UnknownHashError


class PasswordHasher(Protocol):
    def hash(self, plaintext: str) -> str: ...

    def verify(self, plaintext: str, hashed: str) -> bool: ...


class Argon2Hasher:
    def __init__(self) -> None:
        self._context = CryptContext(schemes=["argon2"], deprecated="auto")

    def hash(self, plaintext: str) -> str:
        return self._context.hash(plaintext)

    def verify(self, plaintext: str, hashed: str) -> bool:
        try:
            return self._context.verify(plaintext, hashed)
        except (UnknownHashError, ValueError, TypeError):
            return False
