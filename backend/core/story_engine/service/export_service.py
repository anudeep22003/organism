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


def _grid_positions(
    count: int,
    is_last: bool,
    cols: int,
    rows: int,
    margin: float,
    gutter: float,
    cell_w: float,
    cell_h: float,
    page_w: float,
    page_h: float,
) -> list[tuple[float, float]]:
    """Return (x, y) bottom-left corner for each image slot on a page.

    reportlab uses bottom-left origin; slot 0 is the top-left cell.
    For the last page with fewer than cols*rows images, panels are centred.
    """
    top_y = page_h - margin - cell_h
    bot_y = margin

    # Full-page regular positions (row-major, top-to-bottom, left-to-right)
    regular: list[tuple[float, float]] = [
        (margin, top_y),  # slot 0: top-left
        (margin + cell_w + gutter, top_y),  # slot 1: top-right
        (margin, bot_y),  # slot 2: bottom-left
        (margin + cell_w + gutter, bot_y),  # slot 3: bottom-right
    ]

    if not is_last or count == cols * rows:
        return regular[:count]

    # Last page centring logic
    if count == 1:
        x = (page_w - cell_w) / 2
        return [(x, top_y)]
    elif count == 2:
        total_w = 2 * cell_w + gutter
        x_start = (page_w - total_w) / 2
        return [
            (x_start, top_y),
            (x_start + cell_w + gutter, top_y),
        ]
    else:  # count == 3
        total_w = 2 * cell_w + gutter
        x_start = (page_w - total_w) / 2
        x_centre = (page_w - cell_w) / 2
        return [
            (x_start, top_y),
            (x_start + cell_w + gutter, top_y),
            (x_centre, bot_y),
        ]


def _build_pdf_portrait_a4(image_bytes_list: list[bytes]) -> bytes:
    """
    Portrait A4, 2×2 grid, 10pt margins, 5pt gutter between cells.

    Page:        595×842pt (A4 portrait)
    Margin:      10pt all sides
    Gutter:      5pt between cells
    Cell size:   ~285×406pt (2 cols × 2 rows)

    Images are scaled to fit their cell preserving aspect ratio, then
    centred within the cell.
    """
    from io import BytesIO as _BytesIO

    from PIL import Image as PILImage
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas as rl_canvas

    PAGE_W, PAGE_H = A4  # 595.27 × 841.89
    MARGIN = 10.0
    GUTTER = 5.0
    COLS, ROWS = 2, 2

    usable_w = PAGE_W - 2 * MARGIN
    usable_h = PAGE_H - 2 * MARGIN
    cell_w = (usable_w - (COLS - 1) * GUTTER) / COLS
    cell_h = (usable_h - (ROWS - 1) * GUTTER) / ROWS

    buf = _BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)

    pages = [image_bytes_list[i : i + 4] for i in range(0, len(image_bytes_list), 4)]

    for page_idx, page_images in enumerate(pages):
        is_last = page_idx == len(pages) - 1
        count = len(page_images)

        positions = _grid_positions(
            count,
            is_last,
            COLS,
            ROWS,
            MARGIN,
            GUTTER,
            cell_w,
            cell_h,
            PAGE_W,
            PAGE_H,
        )

        for img_bytes, (cell_x, cell_y) in zip(page_images, positions):
            img = PILImage.open(_BytesIO(img_bytes))
            iw, ih = img.size
            scale = min(cell_w / iw, cell_h / ih)
            dw, dh = iw * scale, ih * scale
            dx = cell_x + (cell_w - dw) / 2
            dy = cell_y + (cell_h - dh) / 2
            c.drawImage(ImageReader(_BytesIO(img_bytes)), dx, dy, dw, dh)

        c.showPage()

    c.save()
    return buf.getvalue()


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

    async def export_as_pdf(self, project_id: uuid.UUID, story_id: uuid.UUID) -> bytes:
        pairs = await self._get_panels_for_export(project_id, story_id)

        # Download all images concurrently
        image_bytes_list: list[bytes] = list(
            await asyncio.gather(
                *[
                    asyncio.to_thread(
                        self.gcs_service.download_as_bytes, image.object_key
                    )
                    for _, image in pairs
                ]
            )
        )

        return await asyncio.to_thread(_build_pdf_portrait_a4, image_bytes_list)

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
