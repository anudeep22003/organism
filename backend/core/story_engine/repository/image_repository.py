import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Image


class ImageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_image(self, image: Image) -> Image:
        self.db.add(image)
        return image

    async def get_image(self, image_id: uuid.UUID) -> Image | None:
        return await self.db.get(Image, image_id)
