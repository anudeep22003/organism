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

    async def _get_reference_images(
        self, target_id: uuid.UUID, discriminator_key: ImageDiscriminatorKey
    ) -> list[Image]:
        """Return all reference images for a target, newest first."""
        result = await self.db.execute(
            select(Image)
            .where(
                Image.target_id == target_id,
                Image.discriminator_key == discriminator_key,
            )
            .order_by(Image.created_at.desc())
        )
        return list(result.scalars().all())

    async def _delete_reference_image(
        self,
        image_id: uuid.UUID,
        target_id: uuid.UUID,
        discriminator_key: ImageDiscriminatorKey,
        target_label: str,
    ) -> None:
        """Delete a single reference image, verifying target ownership and discriminator."""
        image = await self.get_image(image_id)
        if (
            image is None
            or image.target_id != target_id
            or image.discriminator_key != discriminator_key
        ):
            raise NotFoundError(
                f"Reference image {image_id} not found for {target_label} {target_id}"
            )
        await self.db.delete(image)

    async def get_character_reference_images(
        self, character_id: uuid.UUID
    ) -> list[Image]:
        return await self._get_reference_images(
            character_id, ImageDiscriminatorKey.CHARACTER_REFERENCE
        )

    async def get_panel_reference_images(self, panel_id: uuid.UUID) -> list[Image]:
        return await self._get_reference_images(
            panel_id, ImageDiscriminatorKey.PANEL_REFERENCE
        )

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
        await self._delete_reference_image(
            image_id,
            character_id,
            ImageDiscriminatorKey.CHARACTER_REFERENCE,
            "character",
        )

    async def delete_panel_reference_image(
        self, image_id: uuid.UUID, panel_id: uuid.UUID
    ) -> None:
        """Delete a single PANEL_REFERENCE image, verifying it belongs to the panel."""
        await self._delete_reference_image(
            image_id,
            panel_id,
            ImageDiscriminatorKey.PANEL_REFERENCE,
            "panel",
        )
