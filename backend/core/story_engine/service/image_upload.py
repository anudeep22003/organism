from io import BytesIO

from fastapi import UploadFile
from google.cloud.storage import Client  # type: ignore[import-untyped]

from core.config import GCP_PROJECT_ID, GCP_STORAGE_BUCKET

from ..repository import Repository

client = Client(project=GCP_PROJECT_ID)


class ImageUploadService:
    def __init__(self, repository: Repository):
        self.repository = repository
        self.bucket = client.bucket(GCP_STORAGE_BUCKET)

    async def upload_image(self, image: UploadFile) -> str:
        return "yet to be implemented"

    async def _create_in_processing_edit_event(self) -> None:
        raise NotImplementedError("Not implemented")

    def _create_object_key(self) -> str:
        raise NotImplementedError("Not implemented")

    def _create_image_variants(self) -> dict[str, BytesIO]:
        # create thumb, preview and original options using Pillow
        # do we send byte array?
        # cheap way to get size
        # buf.seek(0, 2)     # move head to end
        # size = buf.tell()  # head position == size
        # buf.seek(0)        # rewind for upload
        raise NotImplementedError("Not implemented")

    def _upload_image_to_bucket(self, image: UploadFile) -> str:
        raise NotImplementedError("Not implemented")

    async def _create_image_artefact(self) -> None:
        raise NotImplementedError("Not implemented")

    async def _mark_edit_event_completed(self) -> None:
        raise NotImplementedError("Not implemented")
