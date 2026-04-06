import asyncio
import uuid
import zipfile
from io import BytesIO
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import ExportError
from ..models.image import Image as ImageModel
from ..models.panel import Panel
from ..repository import RepositoryV2
from .image_service import GCSUploadService, get_gcs_upload_service
from .panel_service import PanelService

_FONT_PATH = (
    Path(__file__).parent.parent / "assets" / "fonts" / "Figtree-VariableFont_wght.ttf"
)


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


def _dominant_colour(img: object) -> tuple[int, int, int]:
    """Return the most prevalent RGB colour in img via 8-colour quantisation."""
    from PIL import Image as PILImage

    assert isinstance(img, PILImage.Image)
    thumb = img.resize((50, 50))
    quantized = thumb.convert("P", palette=PILImage.Palette.ADAPTIVE, colors=8)
    counts: list[tuple[int, int]] = quantized.getcolors() or []  # type: ignore[assignment]
    dominant_idx: int = max(counts, key=lambda x: x[0])[1]
    raw_palette = quantized.getpalette() or []
    r = int(raw_palette[dominant_idx * 3])
    g = int(raw_palette[dominant_idx * 3 + 1])
    b = int(raw_palette[dominant_idx * 3 + 2])
    return (r, g, b)


def _luminance(rgb: tuple[int, int, int]) -> float:
    """WCAG relative luminance of an sRGB colour."""

    def _c(val: int) -> float:
        s = val / 255.0
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4

    return 0.2126 * _c(rgb[0]) + 0.7152 * _c(rgb[1]) + 0.0722 * _c(rgb[2])


def _contrast_ratio(fg: tuple[int, int, int], bg: tuple[int, int, int]) -> float:
    lf = _luminance(fg) + 0.05
    lb = _luminance(bg) + 0.05
    return max(lf, lb) / min(lf, lb)


def _compose_panel_image(image_bytes: bytes, dialogue: str) -> bytes:
    """Optionally extend the panel image downward with a dialogue bar.

    If dialogue is empty, returns the image unchanged (no bar added).

    When dialogue is present:
    1. Find dominant colour: resize to 50×50, quantize to 8 colours,
       pick most frequent palette entry.
    2. Compute complementary colour: convert RGB → HSV (colorsys.rgb_to_hsv),
       rotate hue by 0.5 (180°), convert back to RGB.
    3. Pick text colour: try dominant_rgb first (check contrast ≥ 4.5:1).
       Fall back to black or white, whichever has higher contrast.
    4. Bar height: max(60, int(img_height * 0.15))
    5. New canvas: img_width × (img_height + bar_height), fill bar with
       complementary colour, paste original at top.
    6. Draw dialogue text centred in bar using Figtree font. Font size chosen
       to fit within bar width with 10px horizontal padding; cap at 28pt.
    7. Return JPEG bytes.
    """
    # No dialogue → return the image as-is, no bar added
    if not dialogue.strip():
        return image_bytes

    import colorsys

    from PIL import Image as PILImage
    from PIL import ImageDraw, ImageFont

    img = PILImage.open(BytesIO(image_bytes)).convert("RGB")
    iw, ih = img.size

    # 1. Dominant colour
    dominant_rgb = _dominant_colour(img)

    # 2. Complementary colour (HSV hue + 180°)
    r, g, b = (v / 255.0 for v in dominant_rgb)
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    comp_h = (h + 0.5) % 1.0
    cr, cg, cb = colorsys.hsv_to_rgb(comp_h, s, v)
    bar_colour: tuple[int, int, int] = (int(cr * 255), int(cg * 255), int(cb * 255))

    # 3. Text colour — try dominant_rgb first, fall back to black/white
    text_colour: tuple[int, int, int]
    if _contrast_ratio(dominant_rgb, bar_colour) >= 4.5:
        text_colour = dominant_rgb
    else:
        text_colour = (
            (0, 0, 0)
            if _contrast_ratio((0, 0, 0), bar_colour)
            >= _contrast_ratio((255, 255, 255), bar_colour)
            else (255, 255, 255)
        )

    # 4-6. Compose canvas
    bar_h = max(60, int(ih * 0.15))
    canvas = PILImage.new("RGB", (iw, ih + bar_h), bar_colour)
    canvas.paste(img, (0, 0))

    draw = ImageDraw.Draw(canvas)
    padding = 10
    font_size = 28
    font = ImageFont.truetype(str(_FONT_PATH), font_size)
    # Shrink font until text fits within bar width
    while font_size > 8:
        bbox = draw.textbbox((0, 0), dialogue, font=font)
        if bbox[2] - bbox[0] <= iw - 2 * padding:
            break
        font_size -= 1
        font = ImageFont.truetype(str(_FONT_PATH), font_size)
    bbox = draw.textbbox((0, 0), dialogue, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    tx = (iw - text_w) // 2
    ty = ih + (bar_h - text_h) // 2
    draw.text((tx, ty), dialogue, fill=text_colour, font=font)

    out = BytesIO()
    canvas.save(out, format="JPEG", quality=92)
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
                composed = await asyncio.to_thread(
                    _compose_panel_image,
                    img_bytes,
                    panel.attributes.get("dialogue", ""),
                )
                zf.writestr(f"{str(i).zfill(pad)}_panel.jpg", composed)
        return buf.getvalue()

    async def export_as_pdf(self, project_id: uuid.UUID, story_id: uuid.UUID) -> bytes:
        pairs = await self._get_panels_for_export(project_id, story_id)

        # Download all images concurrently
        raw_bytes_list: list[bytes] = list(
            await asyncio.gather(
                *[
                    asyncio.to_thread(
                        self.gcs_service.download_as_bytes, image.object_key
                    )
                    for _, image in pairs
                ]
            )
        )

        # Compose dialogue bars (sequential — CPU-bound but fast for typical counts)
        composed_list: list[bytes] = [
            await asyncio.to_thread(
                _compose_panel_image,
                raw,
                panel.attributes.get("dialogue", ""),
            )
            for (panel, _), raw in zip(pairs, raw_bytes_list)
        ]

        return await asyncio.to_thread(_build_pdf_portrait_a4, composed_list)

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
                composed = await asyncio.to_thread(
                    _compose_panel_image,
                    raw,
                    panel.attributes.get("dialogue", ""),
                )
                instagram = await asyncio.to_thread(_to_instagram_jpeg, composed)
                zf.writestr(f"{str(i).zfill(pad)}_panel.jpg", instagram)
                captions.append(f"Panel {i}: {panel.attributes.get('dialogue', '')}")

            zf.writestr("captions.txt", "\n".join(captions))

        return buf.getvalue()
