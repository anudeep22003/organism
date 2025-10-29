import asyncio
import random

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# from core.config import DATABASE_URL

DATABASE_URL = "postgresql+psycopg://postgres:123456@localhost:5432/dummy"

async_db_engine = create_async_engine(DATABASE_URL, echo=True)

seed_text = "the quick brown fox jumps over the lazy dog"


class Base(DeclarativeBase):
    pass


class DummyTest(Base):
    __tablename__ = "dummy_test"

    id: Mapped[int] = mapped_column(primary_key=True)
    dummy_text: Mapped[str] = mapped_column(
        default=lambda: " ".join(random.choices(seed_text.split(), k=random.randint(10, 1000)))
    )

    def __repr__(self) -> str:
        return f"DummyTest(id={self.id}, dummy_text={self.dummy_text})"


async def create_dummy_tables() -> None:
    async with async_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def create_dummy_data() -> None:
    async with AsyncSession(async_db_engine) as session:
        for i in range(10):
            new_dummy = DummyTest()
            session.add(new_dummy)
            await session.commit()


if __name__ == "__main__":
    asyncio.run(create_dummy_tables())
    asyncio.run(create_dummy_data())
