"""Storage service abstraction for local and S3 storage."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional
import os
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from datetime import timedelta
from app.core.config import settings
import uuid


class StorageService(ABC):
    """Abstract storage service interface."""
    
    @abstractmethod
    def save_file(self, file_data: BinaryIO, filename: str, content_type: str) -> str:
        """
        Save file and return storage key.
        
        Args:
            file_data: File binary data
            filename: Original filename
            content_type: MIME type
            
        Returns:
            Storage key (path or S3 key)
        """
        pass
    
    @abstractmethod
    def delete_file(self, storage_key: str) -> None:
        """
        Delete file by storage key.
        
        Args:
            storage_key: Storage key
        """
        pass
    
    @abstractmethod
    def generate_signed_url(self, storage_key: str, expires_in: int = 3600) -> str:
        """
        Generate signed URL for file access.
        
        Args:
            storage_key: Storage key
            expires_in: URL expiration in seconds
            
        Returns:
            Signed URL
        """
        pass
    
    @abstractmethod
    def file_exists(self, storage_key: str) -> bool:
        """
        Check if file exists.
        
        Args:
            storage_key: Storage key
            
        Returns:
            True if file exists
        """
        pass


class LocalStorageService(StorageService):
    """Local filesystem storage service."""
    
    def __init__(self, upload_dir: str):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def save_file(self, file_data: BinaryIO, filename: str, content_type: str) -> str:
        """Save file to local filesystem."""
        # Generate unique filename
        ext = Path(filename).suffix
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_path = self.upload_dir / unique_filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(file_data.read())
        
        return unique_filename
    
    def delete_file(self, storage_key: str) -> None:
        """Delete file from local filesystem."""
        file_path = self.upload_dir / storage_key
        if file_path.exists():
            file_path.unlink()
    
    def generate_signed_url(self, storage_key: str, expires_in: int = 3600) -> str:
        """Generate URL for local file (simple path)."""
        # In local development, return API endpoint URL
        return f"{settings.BACKEND_URL}/uploads/{storage_key}"
    
    def file_exists(self, storage_key: str) -> bool:
        """Check if file exists locally."""
        file_path = self.upload_dir / storage_key
        return file_path.exists()


class S3StorageService(StorageService):
    """S3-compatible storage service (MinIO/AWS S3)."""
    
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        region: str = "us-east-1",
        use_ssl: bool = True
    ):
        self.bucket = bucket
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=Config(signature_version="s3v4"),
            use_ssl=use_ssl
        )
        
        # Create bucket if it doesn't exist
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
        except ClientError:
            try:
                self.s3_client.create_bucket(Bucket=self.bucket)
            except ClientError as e:
                print(f"Error creating bucket: {e}")
    
    def save_file(self, file_data: BinaryIO, filename: str, content_type: str) -> str:
        """Save file to S3."""
        # Generate unique key
        ext = Path(filename).suffix
        unique_key = f"uploads/{uuid.uuid4()}{ext}"
        
        # Upload to S3
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=unique_key,
            Body=file_data.read(),
            ContentType=content_type
        )
        
        return unique_key
    
    def delete_file(self, storage_key: str) -> None:
        """Delete file from S3."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=storage_key)
        except ClientError as e:
            print(f"Error deleting file: {e}")
    
    def generate_signed_url(self, storage_key: str, expires_in: int = 3600) -> str:
        """Generate presigned URL for S3 object."""
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": storage_key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            print(f"Error generating signed URL: {e}")
            return ""
    
    def file_exists(self, storage_key: str) -> bool:
        """Check if file exists in S3."""
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=storage_key)
            return True
        except ClientError:
            return False


def get_storage_service() -> StorageService:
    """
    Get storage service based on configuration.
    
    Returns:
        StorageService instance
    """
    if settings.STORAGE_TYPE == "s3":
        return S3StorageService(
            endpoint=settings.S3_ENDPOINT,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            bucket=settings.S3_BUCKET,
            region=settings.S3_REGION,
            use_ssl=settings.S3_USE_SSL
        )
    else:
        return LocalStorageService(settings.UPLOAD_DIR)
