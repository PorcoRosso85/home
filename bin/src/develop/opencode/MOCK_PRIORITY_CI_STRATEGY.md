# Mock-Priority CI Smoke Foundation Strategy

## Strategic Foundation Overview

This strategy establishes a **mock-first testing hierarchy** that prioritizes safety, speed, and reliability while maintaining comprehensive coverage of the opencode-client ecosystem.

## Safety Value Analysis

### Mock-First Approach Benefits
- **Zero External Dependencies**: Mock servers eliminate network timeouts, service outages, and authentication complexities during CI runs
- **Predictable Test Environment**: Mock responses guarantee consistent behavior, enabling deterministic test outcomes
- **Isolated Failure Domain**: Test failures indicate actual code issues rather than infrastructure problems
- **Resource Safety**: No risk of exhausting rate limits, consuming API quotas, or triggering production side effects

### Risk Mitigation Strategy
- **Environment Separation**: Mock tests (`CI_TEST_MODE=mock`) provide rapid feedback without external service risks
- **Staged Validation**: Real server tests (`CI_TEST_MODE=server`) reserved for integration and scheduled runs
- **Graceful Degradation**: Mock failures stop builds immediately; server failures generate warnings with fallback guidance

## CI Time Optimization Strategy

### Resource Allocation Matrix
| Test Type | Frequency | Duration | Resources | Trigger |
|-----------|-----------|----------|-----------|---------|
| Mock Tests | Every PR | 30-60s | Minimal CPU/Memory | Push/PR |
| Server Integration | Scheduled (daily) | 3-5min | Network + Server | Schedule/Manual |
| End-to-End | Pre-release | 10-15min | Full Infrastructure | Tag/Release |

### Performance Optimization
- **Parallel Execution**: Mock tests run concurrently with build steps
- **Early Termination**: Mock failures stop pipeline before resource-intensive steps
- **Cached Dependencies**: Mock environments reuse Nix store for sub-second startup

## Goal Achievement Contribution

### "30秒で成功 or 明確な次アクション" Alignment
- **Rapid Feedback Loop**: Mock tests complete in <60s, providing immediate success confirmation
- **Clear Error Messages**: Mock server responses include structured error handling and next-action guidance
- **Deterministic Outcomes**: Eliminates "works on my machine" scenarios through reproducible mock environments

### Core Values Integration
- **Reproducibility**: Fixed mock responses ensure identical behavior across all environments
- **Reliability**: Self-contained tests eliminate flaky network-dependent failures
- **Clear Error Messages**: Mock server includes diagnostic endpoints and structured error responses

## Implementation Approach

### Two-Tier Testing Architecture
```bash
# Tier 1: Mock-Priority (Default for CI)
CI_TEST_MODE=mock ./run_tests.sh  # Fast, isolated, deterministic

# Tier 2: Server Integration (Scheduled/Manual)
CI_TEST_MODE=server ./run_tests.sh  # Comprehensive, real-world validation
```

### Environment Variable Strategy
- **`CI_TEST_MODE=mock`**: Uses existing `session_mock_server.sh` with enhanced endpoints
- **`CI_TEST_MODE=server`**: Requires real opencode server with timeout/retry mechanisms
- **Default Behavior**: Mock mode for safety unless explicitly overridden

### Safety Mechanisms
- **Timeout Enforcement**: Server tests auto-fail after 120s to prevent CI hangs
- **Fallback Documentation**: Server test failures include mock-verified functionality status
- **Health Check Gates**: Server tests require successful mock tests as prerequisites

## Next Steps Implementation Roadmap

1. **Enhance Mock Server**: Extend `session_mock_server.sh` with error scenarios and diagnostic endpoints
2. **CI Integration**: Add `CI_TEST_MODE` environment variable to existing CI workflow
3. **Test Migration**: Convert existing server-dependent tests to mock-compatible versions
4. **Documentation Update**: Add mock-priority testing guidelines to contributor documentation
5. **Monitoring Integration**: Implement scheduled server tests with failure notification

This foundation ensures opencode-client maintains production quality while optimizing for developer velocity and CI resource efficiency.