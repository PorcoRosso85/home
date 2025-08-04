# Incremental Indexing Design

## Change Detection
- Use file mtime for initial filtering (fast)
- Verify with content hash (SHA-256) for accuracy
- Store mtime + hash in persistence layer

## Batch Processing Strategy
- Process changes in configurable batch sizes (default: 100)
- Group by operation type: new/modified/deleted
- Use async I/O for parallel file reading

## Transaction Handling
- Wrap batch updates in single transaction
- Rollback on any failure within batch
- Checkpoint after each successful batch

## Integration with index_flakes_with_persistence
```python
async def incremental_update(db, last_run_time):
    changes = detect_changes(last_run_time)
    for batch in chunk(changes, BATCH_SIZE):
        async with db.transaction():
            await process_batch(batch)
            await update_metadata(batch)
```

Key: Minimize full scans, maximize throughput via batching, ensure consistency through transactions.