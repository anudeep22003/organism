import asyncio
import uuid
import zipfile
from io import BytesIO

from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import ExportError
from ..models.image import Image as ImageModel
from ..models.panel import Panel
from ..repository import RepositoryV2
from .image_service import GCSUploadService, get_gcs_upload_service
from .panel_service import PanelService


def _to_instagram_jpeg(image_bytes: bytes) -> bytes:
    """Resize/pad image to 1080×1080 sRGB JPEG for Instagram carousel."""
    from PIL import Image as PILImage

    img = PILImage.open(BytesIO(image_bytes)).convert("RGB")
    target = 1080
    img.thumbnail((target, target), PILImage.Resampling.LANCZOS)
    canvas = PILImage.new("RGB", (target, target), (255, 255, 255))
    offset = ((target - img.width) // 2, (target - img.height) // 2)
    canvas.paste(img, offset)
    out = BytesIO()
    canvas.save(out, format="JPEG", quality=92, subsampling=0)
    return out.getvalue()


class ExportService:
    def __init__(
        self,
        db_session: AsyncSession,
        panel_service: PanelService | None = None,
        gcs_service: GCSUploadService | None = None,
    ):
        self.db = db_session
        self.repository_v2 = RepositoryV2(db_session)
        self.panel_service = panel_service or PanelService(db_session)
        self.gcs_service = gcs_service or get_gcs_upload_service()

    async def _get_panels_for_export(
        self, project_id: uuid.UUID, story_id: uuid.UUID
    ) -> list[tuple[Panel, ImageModel]]:
        """Return panels with canonical renders, ordered by order_index.

        Raises ExportError listing all positions missing a render.
        """
        pairs = await self.panel_service.get_panels(project_id, story_id)
        missing = [p.order_index for p, r in pairs if r is None]
        if missing:
            raise ExportError(
                f"Panels at positions {missing} have no render — "
                "render all panels before exporting"
            )
        return [(p, r) for p, r in pairs]

    async def export_as_zip(self, project_id: uuid.UUID, story_id: uuid.UUID) -> bytes:
        pairs = await self._get_panels_for_export(project_id, story_id)
        pad = len(str(len(pairs)))

        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, (panel, image) in enumerate(pairs, start=1):
                img_bytes = await asyncio.to_thread(
                    self.gcs_service.download_as_bytes, image.object_key
                )
                zf.writestr(f"{str(i).zfill(pad)}_panel.jpg", img_bytes)
        return buf.getvalue()

    async def export_as_instagram_zip(
        self, project_id: uuid.UUID, story_id: uuid.UUID
    ) -> bytes:
        pairs = await self._get_panels_for_export(project_id, story_id)
        pad = len(str(len(pairs)))
        captions: list[str] = []

        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, (panel, image) in enumerate(pairs, start=1):
                raw = await asyncio.to_thread(
                    self.gcs_service.download_as_bytes, image.object_key
                )
                processed = await asyncio.to_thread(_to_instagram_jpeg, raw)
                zf.writestr(f"{str(i).zfill(pad)}_panel.jpg", processed)
                captions.append(f"Panel {i}: {panel.attributes.get('dialogue', '')}")

            zf.writestr("captions.txt", "\n".join(captions))

        return buf.getvalue()
