from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Image


class ImageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_image(
        self,
        image: Image,
    ) -> Image:
        self.db.add(image)
        return image
