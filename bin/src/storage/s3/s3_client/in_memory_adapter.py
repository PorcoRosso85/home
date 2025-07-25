"""In-memory implementation of StorageAdapter for testing and development."""

from typing import Dict, Optional, List
from datetime import datetime
from .storage_adapter import StorageObject


class InMemoryStorageAdapter:
    """In-memory storage adapter using a dictionary."""
    
    def __init__(self):
        self._storage: Dict[str, bytes] = {}
        self._metadata: Dict[str, Dict[str, str]] = {}
    
    def put_object(self, key: str, body: bytes, metadata: Optional[Dict[str, str]] = None) -> None:
        self._storage[key] = body
        if metadata:
            self._metadata[key] = metadata
    
    def get_object(self, key: str) -> bytes:
        if key not in self._storage:
            raise KeyError(f"Object not found: {key}")
        return self._storage[key]
    
    def delete_object(self, key: str) -> None:
        self._storage.pop(key, None)
        self._metadata.pop(key, None)
    
    def list_objects(self, prefix: str = "") -> List[StorageObject]:
        now = datetime.now().isoformat()
        return sorted([
            StorageObject(
                key=k, 
                size=len(v), 
                last_modified=now,
                metadata=self._metadata.get(k)
            )
            for k, v in self._storage.items() 
            if k.startswith(prefix)
        ], key=lambda x: x.key)
    
    def object_exists(self, key: str) -> bool:
        return key in self._storage
    
    def get_provider_name(self) -> str:
        return "in-memory"