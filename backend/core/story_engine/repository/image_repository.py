import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Image
from ..models.image import ImageFormat, ImageType, ImageVariant


class ImageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_image_entry_in_db(
        self,
        project_id: uuid.UUID,
        user_id: str,
        character_id: uuid.UUID,
        width: int,
        height: int,
        format: ImageFormat,
        object_key: str,
        bucket: str,
        size_bytes: int,
        variant: ImageVariant,
        filename: str,
        image_type: ImageType,
    ) -> Image:
        image = Image(
            project_id=project_id,
            user_id=uuid.UUID(user_id),
            character_id=character_id,
            width=width,
            height=height,
            format=format,
            object_key=object_key,
            bucket=bucket,
            size_bytes=size_bytes,
            variant=variant,
            filename=filename,
            image_type=image_type,
        )
        self.db.add(image)
        return image
