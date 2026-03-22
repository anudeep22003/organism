import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Image
from ..models.image import ImageDiscriminatorKey


class ImageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_image(self, image: Image) -> Image:
        self.db.add(image)
        return image

    async def get_image(self, image_id: uuid.UUID) -> Image | None:
        return await self.db.get(Image, image_id)

    async def get_character_reference_images(
        self, character_id: uuid.UUID
    ) -> list[Image]:
        result = await self.db.execute(
            select(Image)
            .where(
                Image.character_id == character_id,
                Image.discriminator_key == ImageDiscriminatorKey.CHARACTER_REFERENCE,
            )
            .order_by(Image.created_at.desc())
        )
        return list(result.scalars().all())
