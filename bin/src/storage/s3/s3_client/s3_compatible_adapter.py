"""S3-compatible storage adapter using boto3."""

from typing import Optional, List, Dict, Any
import boto3
from botocore.exceptions import ClientError
from .storage_adapter import StorageAdapter, StorageObject


def detect_provider(endpoint_url: Optional[str]) -> str:
    """Detect the S3 provider from endpoint URL."""
    if not endpoint_url:
        return "AWS S3"
    
    endpoint_lower = endpoint_url.lower()
    
    if "localhost" in endpoint_lower or "minio" in endpoint_lower:
        return "MinIO"
    elif "r2.cloudflarestorage.com" in endpoint_lower:
        return "Cloudflare R2"
    elif "backblazeb2.com" in endpoint_lower:
        return "Backblaze B2"
    else:
        return "S3-compatible"


class S3CompatibleAdapter:
    """Adapter for S3-compatible storage using boto3."""
    
    def __init__(self, client: Any, bucket_name: str, endpoint_url: Optional[str] = None):
        self.client = client
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url
        self._provider = detect_provider(endpoint_url)
    
    def put_object(
        self, 
        key: str, 
        body: bytes, 
        metadata: Optional[Dict[str, str]] = None
    ) -> None:
        """Store an object in S3."""
        kwargs = {
            "Bucket": self.bucket_name,
            "Key": key,
            "Body": body
        }
        if metadata:
            kwargs["Metadata"] = metadata
        
        self.client.put_object(**kwargs)
    
    def get_object(self, key: str) -> bytes:
        """Retrieve an object from S3."""
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=key)
            return response['Body'].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise KeyError(f"Object not found: {key}")
            raise
    
    def delete_object(self, key: str) -> None:
        """Delete an object from S3."""
        self.client.delete_object(Bucket=self.bucket_name, Key=key)
    
    def list_objects(self, prefix: str = "") -> List[StorageObject]:
        """List objects with the given prefix."""
        objects = []
        
        paginator = self.client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)
        
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    storage_obj = StorageObject(
                        key=obj['Key'],
                        size=obj['Size'],
                        last_modified=obj['LastModified'].isoformat(),
                        etag=obj.get('ETag', '').strip('"')
                    )
                    objects.append(storage_obj)
        
        return objects
    
    def object_exists(self, key: str) -> bool:
        """Check if an object exists."""
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False
    
    def get_provider_name(self) -> str:
        """Get the name of the storage provider."""
        return self._provider