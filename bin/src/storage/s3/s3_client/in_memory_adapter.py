"""In-memory implementation of StorageAdapter for testing and development."""

from typing import Dict, Optional, List
from datetime import datetime
from .storage_adapter import StorageAdapter, StorageObject


class InMemoryStorageAdapter:
    """In-memory storage adapter using a dictionary."""
    
    def __init__(self):
        self._storage: Dict[str, tuple[bytes, Optional[Dict[str, str]]]] = {}
    
    def put_object(
        self, 
        key: str, 
        body: bytes, 
        metadata: Optional[Dict[str, str]] = None
    ) -> None:
        """Store an object in memory."""
        self._storage[key] = (body, metadata)
    
    def get_object(self, key: str) -> bytes:
        """Retrieve an object from memory."""
        if key not in self._storage:
            raise KeyError(f"Object not found: {key}")
        return self._storage[key][0]
    
    def delete_object(self, key: str) -> None:
        """Delete an object from memory."""
        if key in self._storage:
            del self._storage[key]
    
    def list_objects(self, prefix: str = "") -> List[StorageObject]:
        """List objects with the given prefix."""
        objects = []
        for key, (body, metadata) in self._storage.items():
            if key.startswith(prefix):
                obj = StorageObject(
                    key=key,
                    size=len(body),
                    last_modified=datetime.now().isoformat(),
                    metadata=metadata
                )
                objects.append(obj)
        return sorted(objects, key=lambda x: x.key)
    
    def object_exists(self, key: str) -> bool:
        """Check if an object exists."""
        return key in self._storage
    
    def get_provider_name(self) -> str:
        """Get the name of the storage provider."""
        return "in-memory"