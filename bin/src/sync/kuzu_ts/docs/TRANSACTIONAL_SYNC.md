# TransactionalSyncAdapter Documentation

## Overview

The `TransactionalSyncAdapter` is a wrapper around `WebSocketSync` that adds transaction support for event synchronization. It ensures that events are only sent to remote clients after their containing transaction has been committed.

## Key Features

- **Transaction Buffering**: Events sent during a transaction are buffered until commit
- **Atomic Synchronization**: All events in a transaction are sent together on commit
- **Rollback Support**: Buffered events are discarded if the transaction is rolled back
- **Nested Transactions**: Supports nested transaction with proper event propagation
- **Integration Ready**: Works seamlessly with `TransactionManager` and `EventGroupManager`

## Architecture

```
┌─────────────────────────┐
│   TransactionManager    │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│ TransactionalSyncAdapter├─────►│    WebSocketSync        │
└─────────────────────────┘     └─────────────────────────┘
            │                               │
            ▼                               ▼
    ┌───────────────┐              ┌───────────────┐
    │ Event Buffer  │              │ WebSocket     │
    │ (per transaction)│           │ Connection    │
    └───────────────┘              └───────────────┘
```

## API

### Constructor

```typescript
const adapter = new TransactionalSyncAdapter(webSocketSync: WebSocketSync);
```

### Transaction Methods

#### `beginTransaction(transactionId?: string): string`
Begins a new transaction. Returns the transaction ID.

```typescript
const txId = adapter.beginTransaction();
// or with custom ID
const txId = adapter.beginTransaction("tx_custom_123");
```

#### `commitTransaction(transactionId: string): Promise<void>`
Commits a transaction, sending all buffered events.

```typescript
await adapter.commitTransaction(txId);
```

#### `rollbackTransaction(transactionId: string): Promise<void>`
Rolls back a transaction, discarding all buffered events.

```typescript
await adapter.rollbackTransaction(txId);
```

#### `setTransactionContext(transactionId: string): void`
Sets the current transaction context for subsequent operations.

```typescript
adapter.setTransactionContext("tx_123");
```

#### `clearTransactionContext(): void`
Clears the current transaction context.

```typescript
adapter.clearTransactionContext();
```

### WebSocketSync Methods

All standard `WebSocketSync` methods are available:

- `connect(url: string): Promise<void>`
- `sendEvent(event: TemplateEvent): Promise<void>`
- `onEvent(handler: (event: TemplateEvent) => void): void`
- `disconnect(): void`
- `isConnected(): boolean`
- `getPendingEvents(): Promise<TemplateEvent[]>`

## Usage Examples

### Basic Transaction

```typescript
const adapter = new TransactionalSyncAdapter(webSocketSync);
await adapter.connect("ws://localhost:8080");

// Begin transaction
const txId = adapter.beginTransaction();

try {
  // Send events (buffered)
  await adapter.sendEvent(event1);
  await adapter.sendEvent(event2);
  
  // Commit - events are sent
  await adapter.commitTransaction(txId);
} catch (error) {
  // Rollback - events are discarded
  await adapter.rollbackTransaction(txId);
}
```

### Integration with TransactionManager

```typescript
const result = await transactionManager.executeInTransaction(async (tx) => {
  // Set transaction context
  adapter.setTransactionContext(tx.transactionId);
  
  // Execute operations
  const event = await tx.executeTemplate("CREATE_USER", params);
  await adapter.sendEvent(event);
  
  // Clear context before return
  adapter.clearTransactionContext();
  
  return event;
});
```

### Nested Transactions

```typescript
// Outer transaction
const outerTxId = adapter.beginTransaction();

await adapter.sendEvent(outerEvent);

// Inner transaction
const innerTxId = adapter.beginTransaction();

await adapter.sendEvent(innerEvent);

// Commit inner (events stay buffered in outer)
await adapter.commitTransaction(innerTxId);

// Commit outer (all events sent)
await adapter.commitTransaction(outerTxId);
```

## Implementation Details

### Event Buffering

Events are stored in a `Map<transactionId, TransactionState>` where each transaction maintains its own event buffer:

```typescript
type TransactionState = {
  id: string;
  events: TemplateEvent[];
  parentId?: string;  // For nested transactions
};
```

### Transaction Stack

The adapter maintains a transaction stack to handle nested transactions:

```typescript
private transactionStack: string[] = [];
private currentTransactionId?: string;
```

### Commit Behavior

1. If transaction has no parent: all events are sent immediately
2. If transaction has parent: events are moved to parent's buffer
3. Events are sent in the order they were added

### Rollback Behavior

1. Transaction and all its events are removed from memory
2. No events are sent to the server
3. Parent transactions (if any) are unaffected

## Best Practices

1. **Always clear context**: Clear transaction context before committing to avoid confusion

```typescript
adapter.setTransactionContext(txId);
// ... do work ...
adapter.clearTransactionContext();
await transactionManager.commitTransaction(txId);
```

2. **Handle disconnections**: The adapter respects WebSocket connection state

```typescript
if (adapter.isConnected()) {
  await adapter.sendEvent(event);
}
```

3. **Use with EventGroups**: Combine with EventGroupManager for atomic multi-event operations

```typescript
const eventGroup = await eventGroupManager.createEventGroup(events);
for (const event of events) {
  await adapter.sendEvent(event);
}
```

4. **Error handling**: Always rollback on errors

```typescript
try {
  // transaction work
  await adapter.commitTransaction(txId);
} catch (error) {
  await adapter.rollbackTransaction(txId);
  throw error;
}
```

## Testing

The adapter includes comprehensive tests covering:

- Basic transaction operations
- Nested transactions
- Connection state handling
- Integration with TransactionManager
- Error scenarios

Run tests with:
```bash
deno test tests/transactional_sync_adapter.test.ts
```

## Performance Considerations

- Events are buffered in memory during transactions
- Large transactions may consume significant memory
- Consider transaction size when designing your application
- Nested transactions add minimal overhead

## Future Enhancements

- Transaction timeout support
- Event compression for large transactions
- Persistent transaction state for recovery
- Transaction-aware event replay