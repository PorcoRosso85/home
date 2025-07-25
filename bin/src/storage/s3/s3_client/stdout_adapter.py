"""Stdout adapter for debugging and development."""

import json
from typing import Optional, List, Dict
from datetime import datetime
from .storage_adapter import StorageAdapter, StorageObject


class StdoutStorageAdapter:
    """Storage adapter that outputs operations to stdout."""
    
    def put_object(self, key: str, body: bytes, metadata: Optional[Dict[str, str]] = None) -> None:
        print(json.dumps({
            "operation": "put_object",
            "key": key,
            "size": len(body),
            "metadata": metadata
        }))
    
    def get_object(self, key: str) -> bytes:
        print(json.dumps({"operation": "get_object", "key": key}))
        return b""  # Return empty bytes for compatibility
    
    def delete_object(self, key: str) -> None:
        print(json.dumps({"operation": "delete_object", "key": key}))
    
    def list_objects(self, prefix: str = "") -> List[StorageObject]:
        print(json.dumps({"operation": "list_objects", "prefix": prefix}))
        return []  # Return empty list for compatibility
    
    def object_exists(self, key: str) -> bool:
        print(json.dumps({"operation": "object_exists", "key": key}))
        return False  # Always return False
    
    def get_provider_name(self) -> str:
        return "stdout"