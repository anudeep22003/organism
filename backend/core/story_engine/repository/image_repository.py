import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Image
from ..models.image import ImageDiscriminatorKey
from .exception import NotFoundError


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
                Image.target_id == character_id,
                Image.discriminator_key == ImageDiscriminatorKey.CHARACTER_REFERENCE,
            )
            .order_by(Image.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_canonical_render(
        self, target_id: uuid.UUID, discriminator_key: ImageDiscriminatorKey
    ) -> Image | None:
        """Return the most recently created Image for the given target and discriminator."""
        result = await self.db.execute(
            select(Image)
            .where(
                Image.target_id == target_id,
                Image.discriminator_key == discriminator_key,
            )
            .order_by(Image.created_at.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def delete_images_for_target(
        self, target_id: uuid.UUID, discriminator_key: ImageDiscriminatorKey
    ) -> None:
        """Delete all Image rows for the given target and discriminator key."""
        await self.db.execute(
            delete(Image).where(
                Image.target_id == target_id,
                Image.discriminator_key == discriminator_key,
            )
        )

    async def get_renders_for_target(
        self, target_id: uuid.UUID, discriminator_key: ImageDiscriminatorKey
    ) -> list[Image]:
        """Return all Image rows for the given target and discriminator, newest first."""
        result = await self.db.execute(
            select(Image)
            .where(
                Image.target_id == target_id,
                Image.discriminator_key == discriminator_key,
            )
            .order_by(Image.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_reference_image(
        self, image_id: uuid.UUID, character_id: uuid.UUID
    ) -> None:
        """Delete a single CHARACTER_REFERENCE image, verifying it belongs to the character."""
        image = await self.get_image(image_id)
        if (
            image is None
            or image.target_id != character_id
            or image.discriminator_key != ImageDiscriminatorKey.CHARACTER_REFERENCE
        ):
            raise NotFoundError(
                f"Reference image {image_id} not found for character {character_id}"
            )
        await self.db.delete(image)
