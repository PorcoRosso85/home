# PocketBase SSE Subscription Tests

This directory contains a comprehensive TDD Red phase test suite for PocketBase's real-time SSE (Server-Sent Events) subscriptions without requiring a browser.

## Files

- `test_pocketbase_sse_subscriptions.py` - Complete test suite with 25 tests covering all aspects of SSE functionality
- `TDD_RED_TEST_LIST.md` - Detailed test list with descriptions and implementation requirements
- `pocketbase_sse_client.py` - Implementation stub showing the structure needed to make tests pass
- `README.md` - This file

## Test Categories

1. **SSE Connection Management** (5 tests)
   - Basic connection establishment
   - Authentication support
   - Heartbeat/keep-alive
   - Auto-reconnection
   - Graceful shutdown

2. **Authentication & Authorization** (5 tests)
   - Public collection access
   - Protected collection security
   - Token management
   - Permission-based filtering
   - Token expiration handling

3. **Real-time Event Handling** (5 tests)
   - CREATE event reception
   - UPDATE event reception
   - DELETE event reception
   - Event ordering guarantees
   - Bulk event processing

4. **Error Scenarios & Recovery** (5 tests)
   - Network interruption recovery
   - Malformed event handling
   - Server overload handling
   - Subscription limit enforcement
   - Timeout management

5. **Performance & Scalability** (5 tests)
   - Event latency measurement
   - Concurrent client scaling
   - Event batching efficiency
   - Memory usage stability
   - Throughput under load

## Running the Tests

### Prerequisites

```bash
pip install pytest pytest-asyncio aiohttp psutil
```

### Run all tests (expect all to FAIL in Red phase)
```bash
pytest test_pocketbase_sse_subscriptions.py -v
```

### Run specific test class
```bash
pytest test_pocketbase_sse_subscriptions.py::TestSSEConnectionManagement -v
```

### Run with detailed output
```bash
pytest test_pocketbase_sse_subscriptions.py -v -s
```

## Implementation Path

To make these tests pass:

1. **Implement SSE Parser**
   - Parse SSE format (id, event, data, retry)
   - Handle multiline data fields
   - Error recovery for malformed events

2. **Build Connection Manager**
   - Establish and maintain SSE connections
   - Implement heartbeat monitoring
   - Auto-reconnection with exponential backoff

3. **Add Authentication Layer**
   - Bearer token integration
   - Token refresh mechanism
   - Permission validation

4. **Create Event Handler**
   - Route events to appropriate handlers
   - Maintain event ordering
   - Implement batching for performance

5. **Optimize for Production**
   - Connection pooling
   - Memory management
   - Performance monitoring

## Test Design Principles

- **Async First**: All tests use asyncio for realistic SSE testing
- **Isolation**: Each test is independent and can run in any order
- **Comprehensive**: Covers happy paths, error cases, and edge conditions
- **Performance Aware**: Includes tests for latency, throughput, and scalability
- **Security Focused**: Tests authentication, authorization, and permission filtering

## Example Implementation Usage

```python
# Initialize client
pb = PocketBaseClient("http://localhost:8090")

# Authenticate
await pb.authenticate("user@example.com", "password")

# Subscribe to collection events
sse_client = pb.realtime()
async for event in sse_client.subscribe_to_collection("posts"):
    print(f"Received {event.event}: {event.data}")
```

## Next Steps

1. Set up a local PocketBase instance for testing
2. Implement the SSE client to make tests pass
3. Add integration tests with real PocketBase
4. Create performance benchmarks
5. Document production deployment considerations