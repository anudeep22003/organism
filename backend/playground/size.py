import os
from io import BytesIO

from PIL import Image


def build_jpeg_in_range(min_mb: int = 5, max_mb: int = 8) -> BytesIO:
    min_bytes = min_mb * 1024 * 1024
    max_bytes = max_mb * 1024 * 1024

    for side in (2200, 2600, 3000, 3400, 3800):
        # Random/noisy image gives realistic JPEG sizes
        img = Image.frombytes("RGB", (side, side), os.urandom(side * side * 3))
        for quality in (95, 92, 90, 88, 85):
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=quality, optimize=True)
            size = buf.tell()
            print(f"Size: {size / 1024 / 1024} mb, quality: {quality}, side: {side}")
            if min_bytes <= size <= max_bytes:
                buf.seek(0)
                return buf

    raise ValueError("Could not generate JPEG in target size range")


if __name__ == "__main__":
    buf = build_jpeg_in_range()
    print(buf.tell())
