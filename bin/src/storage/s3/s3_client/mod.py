"""S3 client abstraction module.

This module provides a unified interface for S3-compatible storage systems,
allowing easy switching between different client implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable, List


@dataclass
class S3ClientConfig:
    """Configuration for S3 client."""
    endpoint_url: Optional[str] = None
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    region_name: str = "us-east-1"
    bucket_name: str = "default-bucket"


@runtime_checkable
class S3Client(Protocol):
    """Protocol defining the S3 client interface."""
    
    def put_object(self, key: str, body: bytes) -> None:
        """Store an object in S3."""
        ...
    
    def get_object(self, key: str) -> bytes:
        """Retrieve an object from S3."""
        ...
    
    def delete_object(self, key: str) -> None:
        """Delete an object from S3."""
        ...
    
    def list_objects(self, prefix: str = "") -> List[str]:
        """List objects with the given prefix."""
        ...