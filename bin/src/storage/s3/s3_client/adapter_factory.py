"""Factory for creating storage adapters based on configuration."""

import os
from typing import Optional
import boto3
from .storage_adapter import StorageAdapter
from .in_memory_adapter import InMemoryStorageAdapter
from .s3_compatible_adapter import S3CompatibleAdapter


def create_storage_adapter(adapter_type: Optional[str] = None) -> StorageAdapter:
    """
    Create a storage adapter based on environment configuration.
    
    Args:
        adapter_type: Explicit adapter type ("in-memory", "s3", or None for auto-detect)
    
    Returns:
        StorageAdapter implementation
    
    Environment variables:
        S3_ENDPOINT: S3-compatible endpoint URL (e.g., http://localhost:9000 for MinIO)
        AWS_ACCESS_KEY_ID: Access key for S3
        AWS_SECRET_ACCESS_KEY: Secret key for S3
        S3_BUCKET: Bucket name for S3 operations
    """
    # Force specific adapter type if requested
    if adapter_type == "in-memory":
        return InMemoryStorageAdapter()
    
    # Check for S3 configuration
    access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    endpoint_url = os.environ.get('S3_ENDPOINT')
    bucket_name = os.environ.get('S3_BUCKET')
    
    # Use in-memory if no S3 credentials provided
    if not access_key or adapter_type == "in-memory":
        return InMemoryStorageAdapter()
    
    # Validate S3 configuration
    if not bucket_name:
        raise ValueError("S3_BUCKET environment variable is required for S3 storage")
    
    # Create S3 client
    client_kwargs = {
        'service_name': 's3',
        'aws_access_key_id': access_key,
        'aws_secret_access_key': secret_key,
    }
    
    if endpoint_url:
        client_kwargs['endpoint_url'] = endpoint_url
        # Use path-style addressing for non-AWS S3
        client_kwargs['config'] = boto3.session.Config(
            s3={'addressing_style': 'path'}
        )
    
    client = boto3.client(**client_kwargs)
    
    return S3CompatibleAdapter(
        client=client,
        bucket_name=bucket_name,
        endpoint_url=endpoint_url
    )