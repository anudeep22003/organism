import uuid

from slugify import slugify


def build_upload_reference_filename(raw_filename: str | None) -> str:
    if not raw_filename:
        return str(uuid.uuid4())
    return slugify(raw_filename)
