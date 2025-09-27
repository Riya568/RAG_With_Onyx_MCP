import tempfile
import uuid
from abc import ABC
from abc import abstractmethod
from io import BytesIO
from typing import Any
from typing import cast
from typing import IO

import puremagic
from google.cloud import storage
from google.cloud.exceptions import NotFound
from sqlalchemy.orm import Session

from onyx.configs.app_configs import GCP_PROJECT_ID
from onyx.configs.app_configs import GCP_BUCKET_NAME
from onyx.configs.app_configs import GCP_FILE_STORE_PREFIX
from onyx.configs.constants import FileOrigin
from onyx.db.engine.sql_engine import get_session_with_current_tenant
from onyx.db.engine.sql_engine import get_session_with_current_tenant_if_none
from onyx.db.file_record import delete_filerecord_by_file_id
from onyx.db.file_record import get_filerecord_by_file_id
from onyx.db.file_record import get_filerecord_by_file_id_optional
from onyx.db.file_record import get_filerecord_by_prefix
from onyx.db.file_record import get_filerecord_by_prefix_optional
from onyx.db.file_record import get_filerecord_by_sha256
from onyx.db.file_record import get_filerecord_by_sha256_optional
from onyx.db.file_record import insert_filerecord
from onyx.db.file_record import update_filerecord
from onyx.db.models import FileRecord
from onyx.logger import get_logger

logger = get_logger(__name__)


class GCPFileStore(ABC):
    """GCP Cloud Storage implementation for file storage."""

    def __init__(self, project_id: str, bucket_name: str, prefix: str = ""):
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.prefix = prefix
        self.client = storage.Client(project=project_id)
        self.bucket = self.client.bucket(bucket_name)

    def initialize(self) -> None:
        """Initialize GCP Cloud Storage connection."""
        try:
            # Check if bucket exists and is accessible
            self.bucket.reload()
            logger.info(f"GCP Cloud Storage initialized successfully. Bucket: {self.bucket_name}")
        except NotFound:
            logger.error(f"GCP bucket '{self.bucket_name}' not found")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize GCP Cloud Storage: {e}")
            raise

    def save_file(
        self,
        file_content: bytes,
        file_name: str,
        file_origin: FileOrigin,
        db_session: Session | None = None,
    ) -> str:
        """Save file to GCP Cloud Storage."""
        try:
            # Generate unique file ID
            file_id = str(uuid.uuid4())
            
            # Create blob path
            blob_path = f"{self.prefix}/{file_id}/{file_name}" if self.prefix else f"{file_id}/{file_name}"
            
            # Upload file to GCP
            blob = self.bucket.blob(blob_path)
            blob.upload_from_string(file_content)
            
            # Save file record to database
            if db_session is None:
                db_session = get_session_with_current_tenant()
            
            file_record = FileRecord(
                file_id=file_id,
                file_name=file_name,
                file_path=blob_path,
                file_origin=file_origin,
                file_size=len(file_content),
                file_hash=hash(file_content),
            )
            
            insert_filerecord(db_session, file_record)
            db_session.commit()
            
            logger.info(f"File saved to GCP: {file_name} (ID: {file_id})")
            return file_id
            
        except Exception as e:
            logger.error(f"Failed to save file to GCP: {e}")
            raise

    def load_file(self, file_id: str, db_session: Session | None = None) -> bytes:
        """Load file from GCP Cloud Storage."""
        try:
            if db_session is None:
                db_session = get_session_with_current_tenant()
            
            # Get file record from database
            file_record = get_filerecord_by_file_id(db_session, file_id)
            if not file_record:
                raise FileNotFoundError(f"File not found: {file_id}")
            
            # Download file from GCP
            blob = self.bucket.blob(file_record.file_path)
            file_content = blob.download_as_bytes()
            
            logger.info(f"File loaded from GCP: {file_record.file_name} (ID: {file_id})")
            return file_content
            
        except Exception as e:
            logger.error(f"Failed to load file from GCP: {e}")
            raise

    def delete_file(self, file_id: str, db_session: Session | None = None) -> None:
        """Delete file from GCP Cloud Storage."""
        try:
            if db_session is None:
                db_session = get_session_with_current_tenant()
            
            # Get file record from database
            file_record = get_filerecord_by_file_id(db_session, file_id)
            if not file_record:
                logger.warning(f"File not found for deletion: {file_id}")
                return
            
            # Delete file from GCP
            blob = self.bucket.blob(file_record.file_path)
            blob.delete()
            
            # Delete file record from database
            delete_filerecord_by_file_id(db_session, file_id)
            db_session.commit()
            
            logger.info(f"File deleted from GCP: {file_record.file_name} (ID: {file_id})")
            
        except Exception as e:
            logger.error(f"Failed to delete file from GCP: {e}")
            raise

    def get_file_url(self, file_id: str, db_session: Session | None = None) -> str:
        """Get public URL for file in GCP Cloud Storage."""
        try:
            if db_session is None:
                db_session = get_session_with_current_tenant()
            
            # Get file record from database
            file_record = get_filerecord_by_file_id(db_session, file_id)
            if not file_record:
                raise FileNotFoundError(f"File not found: {file_id}")
            
            # Generate signed URL
            blob = self.bucket.blob(file_record.file_path)
            url = blob.generate_signed_url(expiration=3600)  # 1 hour expiration
            
            return url
            
        except Exception as e:
            logger.error(f"Failed to get file URL from GCP: {e}")
            raise

    def list_files(self, prefix: str = "", db_session: Session | None = None) -> list[dict]:
        """List files in GCP Cloud Storage."""
        try:
            if db_session is None:
                db_session = get_session_with_current_tenant()
            
            # List blobs with prefix
            blobs = self.bucket.list_blobs(prefix=prefix)
            
            files = []
            for blob in blobs:
                files.append({
                    "name": blob.name,
                    "size": blob.size,
                    "created": blob.time_created,
                    "updated": blob.updated,
                })
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files from GCP: {e}")
            raise


def get_gcp_file_store() -> GCPFileStore:
    """Get GCP file store instance."""
    return GCPFileStore(
        project_id=GCP_PROJECT_ID,
        bucket_name=GCP_BUCKET_NAME,
        prefix=GCP_FILE_STORE_PREFIX,
    )
