# FTS Integration Requirements - Protocol-Based Design

## VSS Pattern to Follow

VSS has been refactored to follow function-first architecture with Protocol-based algebraic design.

### Key Design Principles

1. **Protocol-Based Design (Tagless Final Inspired)**
   - Define algebraic interface using Protocol
   - Interpreter pattern for implementation
   - Type-safe structural subtyping

2. **Function-First API with Protocol**
   ```python
   # VSS returns a Protocol implementation
   from vss_kuzu import create_vss, VSSAlgebra
   
   vss: VSSAlgebra = create_vss(in_memory=True)
   result = vss.search("query", limit=10)
   ```

3. **No Classes for Data Storage**
   - All data structures use TypedDict
   - No @dataclass decorators
   - Pure functions for all operations

## Protocol Definition Pattern

### 1. Create protocols.py
```python
from typing import Protocol, List, Dict, Any, runtime_checkable

@runtime_checkable
class FTSAlgebra(Protocol):
    """FTS操作の代数的インターフェース"""
    
    def index(self, documents: List[Dict[str, str]]) -> Dict[str, Any]:
        """ドキュメントをインデックスに追加"""
        ...
    
    def search(self, query: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """ドキュメントを検索"""
        ...
```

### 2. Implement Interpreter Class
```python
class FTSInterpreter:
    """FTS代数のインタープリター実装"""
    
    def __init__(self, config: Any, service_funcs: Dict[str, Callable]):
        self._config = config
        self._service_funcs = service_funcs
    
    def index(self, documents: List[Dict[str, str]]) -> Dict[str, Any]:
        """ドキュメントをインデックス"""
        return self._service_funcs["index_documents"](documents, self._config)
    
    def search(self, query: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """ドキュメントを検索"""
        search_input = {"query": query, "limit": limit}
        search_input.update(kwargs)
        return self._service_funcs["search"](search_input, self._config)
```

### 3. Update create_fts Function
```python
def create_fts_interpreter(config: Any, service_funcs: Dict[str, Callable]) -> FTSAlgebra:
    """FTSインタープリターを作成"""
    return FTSInterpreter(config, service_funcs)

def create_fts(
    db_path: str = "./kuzu_db",
    in_memory: bool = False,
    **kwargs
) -> FTSAlgebra:
    """
    FTS統一APIインスタンスを作成
    
    Returns:
        FTSAlgebra protocol実装
    
    Example:
        fts = create_fts(in_memory=True)
        fts.index([{"id": "1", "title": "Title", "content": "テキスト"}])
        results = fts.search("検索語")
    """
    # ... 設定作成 ...
    service_funcs = create_fts_service(...)
    return create_fts_interpreter(config, service_funcs)
```

## Migration Steps

### 1. Convert Data Classes to TypedDict
```python
# Before
@dataclass
class FTSConfig:
    db_path: str
    in_memory: bool

# After
class FTSConfig(TypedDict):
    db_path: str
    in_memory: bool
```

### 2. Remove Behavior Classes
```python
# Remove this entire class
class FTS:
    def __init__(self, config):
        self.config = config
    
    def search(self, query: str):
        # implementation
```

### 3. Update All Field Access
```python
# Before
config.db_path

# After
config['db_path']
```

### 4. Make VECTOR Extension Mandatory
```python
# Remove graceful fallbacks
if not vector_available:
    raise RuntimeError(
        f"Failed to initialize FTS: {error_msg}. "
        f"Details: {details}"
    )
```

### 5. Update Tests
```python
# Test Protocol compliance
def test_create_fts_returns_protocol():
    fts = create_fts(in_memory=True)
    assert isinstance(fts, FTSAlgebra)
    assert hasattr(fts, 'index')
    assert hasattr(fts, 'search')
    assert callable(fts.index)
    assert callable(fts.search)
```

### 6. Update __init__.py
```python
__all__ = [
    # Type definitions
    "FTSAlgebra",
    "SearchResult",
    "IndexResult",
    
    # Factory function
    "create_fts",
    
    # Version
    "__version__",
]
```

## Benefits of Protocol Approach

1. **Type Safety**: Protocol provides compile-time interface checking
2. **Flexibility**: Multiple implementations can satisfy the same Protocol
3. **Testability**: Easy to create test doubles that implement the Protocol
4. **Composability**: Protocols can be composed and extended
5. **Algebraic Design**: Inspired by functional programming patterns like Tagless Final

## Example: Complete Migration

### Before (Class-based)
```python
@dataclass
class SearchResult:
    results: List[Dict]
    total: int

class FTS:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = create_connection(db_path)
    
    def search(self, query: str, limit: int = 10) -> SearchResult:
        results = self.connection.execute(...)
        return SearchResult(results=results, total=len(results))
```

### After (Protocol-based)
```python
# protocols.py
@runtime_checkable
class FTSAlgebra(Protocol):
    def search(self, query: str, limit: int = 10, **kwargs) -> Dict[str, Any]: ...

# types.py
class SearchResult(TypedDict):
    ok: bool
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any]

# application.py
class FTSInterpreter:
    def __init__(self, config: Dict[str, Any], service_funcs: Dict[str, Callable]):
        self._config = config
        self._service_funcs = service_funcs
    
    def search(self, query: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        return self._service_funcs["search"](
            {"query": query, "limit": limit, **kwargs}, 
            self._config
        )

def create_fts(db_path: str = "./kuzu_db", **kwargs) -> FTSAlgebra:
    config = {"db_path": db_path, **kwargs}
    service_funcs = create_fts_service(...)
    return FTSInterpreter(config, service_funcs)
```

## Testing Pattern

```python
# Test the Protocol implementation
def test_fts_implements_protocol():
    fts = create_fts(in_memory=True)
    
    # Protocol check
    assert isinstance(fts, FTSAlgebra)
    
    # Test basic operations
    result = fts.index([{"id": "1", "content": "test"}])
    assert result["ok"] is True
    
    search_result = fts.search("test")
    assert search_result["ok"] is True
    assert "results" in search_result
```

## Summary

The Protocol-based approach provides a clean, type-safe, and algebraic design that:
- Separates interface from implementation
- Enables multiple implementations of the same algebra
- Provides better composability and testability
- Follows functional programming principles
- Maintains backward compatibility through the same method signatures