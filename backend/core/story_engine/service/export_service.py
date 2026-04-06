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
