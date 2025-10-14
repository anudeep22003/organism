from pathlib import Path
from typing import List, Optional, Union

from google.cloud.exceptions import NotFound
from google.cloud.storage import Client  # type: ignore[import-untyped]

from core.config import BUCKET_NAME
from core.logging import logger

logger = logger.bind(name=__name__)


class StorageBucketClient:
    """
    Comprehensive Google Cloud Storage client for repository management.

    Supports uploading entire directories, checking file existence,
    reading files, and managing repository structures in GCS.
    """

    def __init__(self, bucket_name: Optional[str] = None):
        """Initialize the storage client with bucket configuration."""
        self.client = Client()
        self.bucket_name = bucket_name or BUCKET_NAME
        self.bucket = self.client.bucket(self.bucket_name)

    def create_folder(self, blob_prefix: str) -> None:
        """Create a folder in the storage bucket.

        Args:
            blob_prefix: Prefix for the folder in the bucket
        """
        self.bucket.blob(blob_prefix).upload_from_string("", content_type="text/plain")

    def upload_file(self, local_file_path: Union[str, Path], blob_name: str) -> None:
        """
        Upload a single file to the storage bucket.

        Args:
            local_file_path: Path to the local file to upload
            blob_name: Name/path for the blob in the bucket
        """
        local_path = Path(local_file_path)
        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        blob = self.bucket.blob(blob_name)
        blob.upload_from_filename(str(local_path))
        logger.info(
            f"Uploaded file: {local_path} -> gs://{self.bucket_name}/{blob_name}"
        )

    def upload_directory(
        self,
        local_dir_path: Union[str, Path],
        blob_prefix: str,
        exclude_patterns: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Upload an entire directory tree to the storage bucket.

        Args:
            local_dir_path: Path to the local directory to upload
            blob_prefix: Prefix for all blobs (e.g., 'repo-name/')
            exclude_patterns: List of patterns to exclude (e.g., ['.git', '*.pyc'])

        Returns:
            List of uploaded blob names
        """
        local_path = Path(local_dir_path)
        if not local_path.is_dir():
            raise NotADirectoryError(f"Directory not found: {local_path}")

        exclude_patterns = exclude_patterns or [
            ".git",
            "__pycache__",
            "*.pyc",
            ".DS_Store",
        ]
        uploaded_files = []

        # Ensure blob_prefix ends with /
        if blob_prefix and not blob_prefix.endswith("/"):
            blob_prefix += "/"

        for file_path in local_path.rglob("*"):
            if file_path.is_file():
                # Check if file should be excluded
                if self._should_exclude_file(file_path, exclude_patterns):
                    continue

                # Calculate relative path from the base directory
                relative_path = file_path.relative_to(local_path)
                blob_name = f"{blob_prefix}{relative_path}".replace("\\", "/")

                try:
                    self.upload_file(file_path, blob_name)
                    uploaded_files.append(blob_name)
                except Exception as e:
                    logger.error(f"Failed to upload {file_path}: {e}")

        logger.info(f"Uploaded {len(uploaded_files)} files from {local_path}")
        return uploaded_files

    def upload_text(self, content: str, blob_name: str) -> None:
        """
        Upload text content directly to a blob.

        Args:
            content: Text content to upload
            blob_name: Name/path for the blob in the bucket
        """
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(content, content_type="text/plain")
        logger.info(f"Uploaded text content to: gs://{self.bucket_name}/{blob_name}")

    def download_file(self, blob_name: str, local_file_path: Union[str, Path]) -> None:
        """
        Download a file from the storage bucket.

        Args:
            blob_name: Name/path of the blob in the bucket
            local_file_path: Path where to save the downloaded file
        """
        local_path = Path(local_file_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        blob = self.bucket.blob(blob_name)
        blob.download_to_filename(str(local_path))
        logger.info(f"Downloaded: gs://{self.bucket_name}/{blob_name} -> {local_path}")

    def read_text(self, blob_name: str) -> str:
        """
        Read text content from a blob.

        Args:
            blob_name: Name/path of the blob in the bucket

        Returns:
            Text content of the blob

        Raises:
            NotFound: If the blob doesn't exist
        """
        blob = self.bucket.blob(blob_name)
        try:
            content = blob.download_as_text()
            logger.info(f"Read text from: gs://{self.bucket_name}/{blob_name}")
            return content
        except NotFound:
            logger.warning(f"Blob not found: gs://{self.bucket_name}/{blob_name}")
            raise

    def exists(self, blob_name: str) -> bool:
        """
        Check if a blob exists in the storage bucket.

        Args:
            blob_name: Name/path of the blob to check

        Returns:
            True if the blob exists, False otherwise
        """
        blob = self.bucket.blob(blob_name)
        exists = blob.exists()
        logger.debug(
            f"Existence check for gs://{self.bucket_name}/{blob_name}: {exists}"
        )
        return exists

    def list_blobs(
        self, prefix: str = "", delimiter: Optional[str] = None
    ) -> List[str]:
        """
        List blobs in the bucket with optional prefix filtering.

        Args:
            prefix: Prefix to filter blobs (e.g., 'repo-name/')
            delimiter: Delimiter for hierarchical listing (e.g., '/')

        Returns:
            List of blob names
        """
        blobs = self.client.list_blobs(
            self.bucket_name, prefix=prefix, delimiter=delimiter
        )
        blob_names = [blob.name for blob in blobs]
        logger.info(f"Listed {len(blob_names)} blobs with prefix: {prefix}")
        return blob_names

    def delete_blob(self, blob_name: str) -> None:
        """
        Delete a blob from the storage bucket.

        Args:
            blob_name: Name/path of the blob to delete
        """
        blob = self.bucket.blob(blob_name)
        blob.delete()
        logger.info(f"Deleted blob: gs://{self.bucket_name}/{blob_name}")

    def delete_directory(self, prefix: str) -> int:
        """
        Delete all blobs with a given prefix (effectively deleting a directory).

        Args:
            prefix: Prefix of blobs to delete (e.g., 'repo-name/')

        Returns:
            Number of blobs deleted
        """
        blobs = self.list_blobs(prefix=prefix)
        deleted_count = 0

        for blob_name in blobs:
            try:
                self.delete_blob(blob_name)
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete {blob_name}: {e}")

        logger.info(f"Deleted {deleted_count} blobs with prefix: {prefix}")
        return deleted_count

    def _should_exclude_file(
        self, file_path: Path, exclude_patterns: List[str]
    ) -> bool:
        """
        Check if a file should be excluded based on patterns.

        Args:
            file_path: Path to the file
            exclude_patterns: List of patterns to match against

        Returns:
            True if file should be excluded, False otherwise
        """
        file_str = str(file_path)
        file_name = file_path.name

        for pattern in exclude_patterns:
            if pattern.startswith("*"):
                # Handle wildcard patterns
                if file_name.endswith(pattern[1:]):
                    return True
            elif pattern in file_str or pattern == file_name:
                return True
            elif any(part == pattern for part in file_path.parts):
                return True

        return False


# Convenience function to get a configured storage client
def get_storage_client() -> StorageBucketClient:
    """Get a configured storage client instance."""
    return StorageBucketClient()
