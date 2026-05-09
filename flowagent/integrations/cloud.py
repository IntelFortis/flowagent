"""
Cloud - Cloud service integrations for FlowAgent.

This module provides integrations with popular cloud providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, BinaryIO, Dict, List, Optional, TypeVar, Union

from flowagent.core.logger import logger
from flowagent.core.exceptions import IntegrationError

T = TypeVar("T")


@dataclass
class CloudConfig:
    """Configuration for cloud services."""
    provider: str = ""
    region: str = ""
    access_key: str = ""
    secret_key: str = ""
    session_token: Optional[str] = None
    endpoint: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class CloudProvider(ABC):
    """
    Abstract base class for cloud providers.

    All cloud integrations should inherit from this class.
    """

    def __init__(self, config: CloudConfig):
        self.config = config
        self._client = None

    @abstractmethod
    async def upload(
        self,
        bucket: str,
        key: str,
        data: Union[bytes, BinaryIO],
        content_type: Optional[str] = None,
    ) -> str:
        """
        Upload data to cloud storage.

        Args:
            bucket: Bucket/container name
            key: Object key
            data: Data to upload
            content_type: Content type

        Returns:
            URL or identifier
        """
        pass

    @abstractmethod
    async def download(
        self,
        bucket: str,
        key: str,
    ) -> bytes:
        """
        Download data from cloud storage.

        Args:
            bucket: Bucket/container name
            key: Object key

        Returns:
            Downloaded data
        """
        pass

    @abstractmethod
    async def delete(
        self,
        bucket: str,
        key: str,
    ) -> None:
        """
        Delete an object from cloud storage.

        Args:
            bucket: Bucket/container name
            key: Object key
        """
        pass

    @abstractmethod
    async def list(
        self,
        bucket: str,
        prefix: Optional[str] = None,
    ) -> List[str]:
        """
        List objects in a bucket.

        Args:
            bucket: Bucket/container name
            prefix: Key prefix filter

        Returns:
            List of object keys
        """
        pass

    @abstractmethod
    async def exists(
        self,
        bucket: str,
        key: str,
    ) -> bool:
        """
        Check if an object exists.

        Args:
            bucket: Bucket/container name
            key: Object key

        Returns:
            True if object exists
        """
        pass


class AWS(CloudProvider):
    """
    AWS cloud provider.

    Example:
        >>> async with AWS(access_key="...", secret_key="...") as aws:
        ...     url = await aws.upload("my-bucket", "file.txt", data)
    """

    def __init__(self, config: Optional[CloudConfig] = None, **kwargs):
        if config is None:
            config = CloudConfig(**kwargs)
        super().__init__(config)

    async def _get_client(self, service: str):
        """Get AWS service client."""
        try:
            import boto3
            from botocore.config import Config

            session = boto3.Session(
                aws_access_key_id=self.config.access_key,
                aws_secret_access_key=self.config.secret_key,
                aws_session_token=self.config.session_token,
                region_name=self.config.region,
            )

            config = Config(
                retries={"max_attempts": 3, "mode": "adaptive"},
            )

            if self.config.endpoint:
                return session.client(
                    service,
                    endpoint_url=self.config.endpoint,
                    config=config,
                )

            return session.client(service, config=config)

        except ImportError:
            raise IntegrationError(
                "boto3 package not installed. "
                "Install this local package with the cloud extra: pip install -e '.[cloud]'"
            )

    async def upload(
        self,
        bucket: str,
        key: str,
        data: Union[bytes, BinaryIO],
        content_type: Optional[str] = None,
    ) -> str:
        """Upload to S3."""
        s3 = await self._get_client("s3")

        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        if isinstance(data, bytes):
            from io import BytesIO
            data = BytesIO(data)

        s3.upload_fileobj(data, bucket, key, ExtraArgs=extra_args)

        url = f"https://{bucket}.s3.{self.config.region}.amazonaws.com/{key}"
        logger.info(f"Uploaded to S3: {url}")
        return url

    async def download(self, bucket: str, key: str) -> bytes:
        """Download from S3."""
        s3 = await self._get_client("s3")

        from io import BytesIO
        buffer = BytesIO()
        s3.download_fileobj(bucket, key, buffer)
        buffer.seek(0)

        return buffer.read()

    async def delete(self, bucket: str, key: str) -> None:
        """Delete from S3."""
        s3 = await self._get_client("s3")
        s3.delete_object(Bucket=bucket, Key=key)
        logger.info(f"Deleted from S3: {bucket}/{key}")

    async def list(self, bucket: str, prefix: Optional[str] = None) -> List[str]:
        """List objects in S3."""
        s3 = await self._get_client("s3")

        params = {"Bucket": bucket}
        if prefix:
            params["Prefix"] = prefix

        response = s3.list_objects_v2(**params)
        return [obj["Key"] for obj in response.get("Contents", [])]

    async def exists(self, bucket: str, key: str) -> bool:
        """Check if object exists in S3."""
        s3 = await self._get_client("s3")

        try:
            s3.head_object(Bucket=bucket, Key=key)
            return True
        except Exception:
            return False


class GoogleCloud(CloudProvider):
    """
    Google Cloud provider.

    Example:
        >>> async with GoogleCloud() as gcs:
        ...     url = await gcs.upload("my-bucket", "file.txt", data)
    """

    def __init__(self, config: Optional[CloudConfig] = None, **kwargs):
        if config is None:
            config = CloudConfig(**kwargs)
        super().__init__(config)

    async def _get_client(self):
        """Get GCS client."""
        try:
            from google.cloud import storage

            if self.config.access_key:
                # Use service account
                import json
                from google.oauth2 import service_account

                credentials = service_account.Credentials.from_service_account_info(
                    json.loads(self.config.access_key)
                )
                return storage.Client(credentials=credentials)

            return storage.Client()

        except ImportError:
            raise IntegrationError(
                "google-cloud-storage package not installed. "
                "Install this local package with the cloud extra: pip install -e '.[cloud]'"
            )

    async def upload(
        self,
        bucket: str,
        key: str,
        data: Union[bytes, BinaryIO],
        content_type: Optional[str] = None,
    ) -> str:
        """Upload to GCS."""
        client = await self._get_client()
        bucket_obj = client.bucket(bucket)
        blob = bucket_obj.blob(key)

        if isinstance(data, bytes):
            data = io.BytesIO(data)

        if content_type:
            blob.upload_from_file(data, content_type=content_type)
        else:
            blob.upload_from_file(data)

        url = f"gs://{bucket}/{key}"
        logger.info(f"Uploaded to GCS: {url}")
        return url

    async def download(self, bucket: str, key: str) -> bytes:
        """Download from GCS."""
        client = await self._get_client()
        bucket_obj = client.bucket(bucket)
        blob = bucket_obj.blob(key)

        return blob.download_as_bytes()

    async def delete(self, bucket: str, key: str) -> None:
        """Delete from GCS."""
        client = await self._get_client()
        bucket_obj = client.bucket(bucket)
        blob = bucket_obj.blob(key)
        blob.delete()
        logger.info(f"Deleted from GCS: {bucket}/{key}")

    async def list(self, bucket: str, prefix: Optional[str] = None) -> List[str]:
        """List objects in GCS."""
        client = await self._get_client()
        bucket_obj = client.bucket(bucket)

        blobs = bucket_obj.list_blobs(prefix=prefix)
        return [blob.name for blob in blobs]

    async def exists(self, bucket: str, key: str) -> bool:
        """Check if object exists in GCS."""
        client = await self._get_client()
        bucket_obj = client.bucket(bucket)
        blob = bucket_obj.blob(key)

        return blob.exists()


class Azure(CloudProvider):
    """
    Azure cloud provider.

    Example:
        >>> async with Azure() as azure:
        ...     url = await azure.upload("my-container", "file.txt", data)
    """

    def __init__(self, config: Optional[CloudConfig] = None, **kwargs):
        if config is None:
            config = CloudConfig(**kwargs)
        super().__init__(config)

    async def _get_client(self):
        """Get Azure Blob client."""
        try:
            from azure.storage.blob import BlobServiceClient

            if self.config.connection_string:
                return BlobServiceClient.from_connection_string(
                    self.config.connection_string
                )

            return BlobServiceClient(
                account_url=f"https://{self.config.access_key}.blob.core.windows.net",
                credential=self.config.secret_key,
            )

        except ImportError:
            raise IntegrationError(
                "azure-storage-blob package not installed. "
                "Install this local package with the cloud extra: pip install -e '.[cloud]'"
            )

    async def upload(
        self,
        bucket: str,
        key: str,
        data: Union[bytes, BinaryIO],
        content_type: Optional[str] = None,
    ) -> str:
        """Upload to Azure Blob."""
        client = await self._get_client()
        container_client = client.get_container_client(bucket)
        blob_client = container_client.get_blob_client(key)

        if isinstance(data, bytes):
            data = io.BytesIO(data)

        extra_args = {}
        if content_type:
            extra_args["content_type"] = content_type

        blob_client.upload_blob(data, **extra_args)

        url = f"https://{self.config.access_key}.blob.core.windows.net/{bucket}/{key}"
        logger.info(f"Uploaded to Azure: {url}")
        return url

    async def download(self, bucket: str, key: str) -> bytes:
        """Download from Azure Blob."""
        client = await self._get_client()
        container_client = client.get_container_client(bucket)
        blob_client = container_client.get_blob_client(key)

        download = blob_client.download_blob()
        return download.readall()

    async def delete(self, bucket: str, key: str) -> None:
        """Delete from Azure Blob."""
        client = await self._get_client()
        container_client = client.get_container_client(bucket)
        blob_client = container_client.get_blob_client(key)
        blob_client.delete_blob()
        logger.info(f"Deleted from Azure: {bucket}/{key}")

    async def list(self, bucket: str, prefix: Optional[str] = None) -> List[str]:
        """List objects in Azure Blob."""
        client = await self._get_client()
        container_client = client.get_container_client(bucket)

        blobs = container_client.list_blobs(name_starts_with=prefix)
        return [blob.name for blob in blobs]

    async def exists(self, bucket: str, key: str) -> bool:
        """Check if object exists in Azure Blob."""
        client = await self._get_client()
        container_client = client.get_container_client(bucket)
        blob_client = container_client.get_blob_client(key)

        return blob_client.exists()


# Import io for BytesIO
import io
