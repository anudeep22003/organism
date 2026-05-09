from sqlalchemy.orm import DeclarativeBase

from core.common import shared_metadata


class StripeORMBase(DeclarativeBase):
    metadata = shared_metadata
    __table_args__ = {"schema": "stripe"}
