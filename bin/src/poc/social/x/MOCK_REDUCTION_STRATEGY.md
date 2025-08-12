# Mock Reduction Strategy

## Current Violation
- **Mock Usage**: 33% of tests use mocking (violates convention)
- **Convention**: "モックは最小限のみ例外的に許可する" (mocks only as minimal exceptions)

## Migration Strategy

### 1. Domain Tests (Zero Mocks)
- Pure logic testing with real objects
- Tweet.spec.ts: Use actual Tweet instances, no mocks
- Focus on business rules and data transformations

### 2. Integration Tests (HTTP Stub Server)
- Replace module mocks with HTTP stub servers (msw)
- client.spec.ts → HTTP interceptors for Twitter API
- Real network layer, controlled responses
- Test actual HTTP client behavior

### 3. E2E Tests (Real API)
- Use live Twitter API with rate limit awareness
- Implement retry logic and request throttling
- Cache responses for repeated test runs
- real_api.spec.ts: Add rate limit handling

## Action Items
1. Remove mocks from domain layer tests
2. Implement msw for integration tests
3. Add rate limiting to E2E tests
4. Update test documentation

Target: Reduce mock usage to <10% (emergency cases only)