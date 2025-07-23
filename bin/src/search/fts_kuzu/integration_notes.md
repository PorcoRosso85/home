# FTS Package Integration Notes

## Package Structure Verification

The FTS package has been successfully restructured to be a proper Python package:

- Import path: `from fts_kuzu import create_fts`
- Package structure follows the VSSパッケージ pattern
- All tests passing in the nix develop environment

## API Verification

The unified API is working correctly:
- `create_fts(in_memory=True)` creates an in-memory FTS instance
- `index()` method accepts documents with 'id' and 'content' fields
- `search()` returns a Result type with:
  - `ok`: boolean status
  - `results`: list of matching documents
  - `metadata`: search metadata including query and timing

## Integration Points for requirement/graph

When integrating from requirement/graph:

1. **Import**: Add `fts-kuzu` to the flake inputs:
   ```nix
   inputs.fts-kuzu.url = "path:../search/fts_kuzu";
   ```

2. **Python Import**:
   ```python
   from fts_kuzu import create_fts
   ```

3. **Usage Pattern**:
   ```python
   # Create FTS service (can be shared)
   fts = create_fts(database_path="/path/to/fts.db")
   
   # Index requirements
   fts.index([
       {"id": req_id, "content": f"{req.name} {req.description}"}
       for req_id, req in requirements.items()
   ])
   
   # Search
   result = fts.search("authentication")
   if result["ok"]:
       for match in result["results"]:
           print(f"Found: {match['id']} (score: {match['score']})")
   ```

## Notes

- The package creates a new KuzuDB instance for each operation (as seen in logs)
- This is by design for isolation, but for production use, consider connection pooling
- The unified API successfully abstracts the underlying KuzuDB implementation