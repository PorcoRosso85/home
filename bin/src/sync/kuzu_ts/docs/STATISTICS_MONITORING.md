# Statistics Monitoring in SyncKuzuClient

## Overview

The `SyncKuzuClient` now includes comprehensive statistics monitoring capabilities that track DML operations at both overall and template-specific levels.

## Features Implemented

### 1. Periodic Stats Reporter
- Automatically logs DML statistics every 5 seconds
- Provides both overall and template-specific metrics
- Includes success rate calculations
- Logs final statistics on client close

### 2. Template-Specific Counters
The system tracks the following metrics for each template type:
- **sent**: Number of events sent via WebSocket
- **received**: Number of events received from remote sources
- **applied**: Number of events successfully applied to local KuzuDB
- **failed**: Number of events that failed to apply
- **successRate**: Percentage of successfully applied events

### 3. Statistics API

#### Get Overall Stats
```typescript
const stats = client.getDMLStats();
// Returns: { sent, received, applied, failed, clientId }
```

#### Get Detailed Stats by Template
```typescript
const detailedStats = client.getDetailedStatsByTemplate();
// Returns: Record<template, { sent, received, applied, failed, successRate }>
```

## Implementation Details

### Stats Storage
- Overall stats tracked in `dmlStats` object
- Template-specific stats stored in `templateStats` Map
- Stats updated in real-time as operations occur

### Periodic Reporting
- Uses `setInterval` with 5-second intervals
- Logs comprehensive report including:
  - Timestamp
  - Client ID
  - Overall statistics with success rate
  - Breakdown by template type

### Example Output
```
=== DML Statistics Report ===
timestamp: 2024-01-28T10:30:45.123Z
clientId: stats-demo-client
overall: {
  sent: 25,
  received: 20,
  applied: 18,
  failed: 2,
  successRate: 90
}
byTemplate: {
  CREATE_USER: { sent: 10, received: 8, applied: 8, failed: 0, successRate: 100% },
  UPDATE_USER: { sent: 8, received: 7, applied: 6, failed: 1, successRate: 85.71% },
  INCREMENT_COUNTER: { sent: 7, received: 5, applied: 4, failed: 1, successRate: 80% }
}
```

## Usage

### Basic Usage
```typescript
const client = new SyncKuzuClient({
  clientId: "my-client",
  autoReconnect: true
});

await client.initialize();
await client.connect();

// Stats reporter starts automatically
// Execute operations...

// Get stats at any time
const stats = client.getDMLStats();
const detailedStats = client.getDetailedStatsByTemplate();

await client.close(); // Logs final stats
```

### Demo Scripts
- `examples/stats_monitoring.ts` - Full example with real KuzuDB
- `examples/stats_monitoring_demo.ts` - Mock-based demo for visualization

### Running the Demo
```bash
deno run --allow-net --allow-read examples/stats_monitoring_demo.ts
```

## Testing

Unit tests are provided in `tests/sync_kuzu_client_stats_unit.test.ts` that verify:
- Template-specific counter tracking
- Overall statistics calculation
- Success rate computation
- Stats reporter lifecycle

Run tests with:
```bash
deno test tests/sync_kuzu_client_stats_unit.test.ts --allow-all --no-check
```

## Architecture Notes

The implementation integrates seamlessly with the existing sync architecture:
1. Stats are updated during normal operation flow
2. No performance impact on DML operations
3. Memory-efficient Map-based storage for template stats
4. Automatic cleanup on client close