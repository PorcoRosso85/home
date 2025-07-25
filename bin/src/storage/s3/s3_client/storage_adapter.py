"""Storage adapter interface for S3-compatible storage backends."""

from typing import Protocol, Optional, Dict, Any, List, runtime_checkable
from dataclasses import dataclass


@dataclass
class StorageObject:
    """Represents an object in storage."""
    key: str
    size: int
    last_modified: str
    etag: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


@runtime_checkable
class StorageAdapter(Protocol):
    """Protocol for storage adapters supporting multiple backends."""
    
    def put_object(
        self, 
        key: str, 
        body: bytes, 
        metadata: Optional[Dict[str, str]] = None
    ) -> None:
        """Store an object in the storage backend."""
        ...
    
    def get_object(self, key: str) -> bytes:
        """Retrieve an object from storage."""
        ...
    
    def delete_object(self, key: str) -> None:
        """Delete an object from storage."""
        ...
    
    def list_objects(self, prefix: str = "") -> List[StorageObject]:
        """List objects with the given prefix."""
        ...
    
    def object_exists(self, key: str) -> bool:
        """Check if an object exists."""
        ...
    
    def get_provider_name(self) -> str:
        """Get the name of the storage provider."""
        ...