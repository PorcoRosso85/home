# Multi-Agent Template for OpenCode

This directory contains a multi-agent system template for OpenCode, providing scripts for orchestrating multiple agents, managing sessions, and handling messages between agents.

## Components

- `orchestrator.sh` - Main orchestrator for coordinating multiple agents
- `session-manager.sh` - Manages agent sessions and state
- `message.sh` - Handles message passing between agents
- `multi-server-manager.sh` - Manages multiple server instances with load balancing
- `unified-error-handler.sh` - Centralized error handling and recovery

## Development Environment

This project uses Nix flakes for reproducible development environments. The development shell provides all necessary dependencies including:

- `opencode` - OpenCode CLI tool
- `curl` - HTTP client for API interactions
- `jq` - JSON processor for parsing API responses
- `netcat-gnu` - Network utility for test mocking (provides GNU nc with `-c` option support)

### Prerequisites

**⚠️ CRITICAL: GNU netcat Requirement**

This template **requires GNU netcat** and will **NOT work with BSD netcat**:

- **✅ Required**: GNU netcat (version 0.7.1+) with `-c` option support
- **❌ Not compatible**: BSD netcat (lacks `-c` option for command execution)
- **🔧 Auto-provided**: `nix develop` automatically installs `netcat-gnu`

**Technical Details:**
- Tests use `nc -l -p <port> -c '<command>'` to create mock HTTP servers
- The `-c` option executes shell commands for each connection 
- BSD netcat doesn't support `-c`, causing tests to fail silently
- Without GNU netcat, you'll see "netcat: invalid option -- 'c'" errors

### Setup

To enter the development environment:

```bash
# From the opencode root directory (../../)
nix develop
```

### Environment Variables

The following environment variables can be configured for testing and development:

```bash
# Required for OpenCode API interactions
export OPENCODE_URL="http://127.0.0.1:4096"        # Default server URL
export OPENCODE_PROVIDER="anthropic"               # AI provider
export OPENCODE_MODEL="claude-3-5-sonnet"          # Specific model

# Optional configuration
export XDG_STATE_HOME="$HOME/.local/state"         # Session storage location
export OPENCODE_TIMEOUT="30"                       # API timeout in seconds
export OPENCODE_PROJECT="multi-agent"              # Default project name
```

### PATH Injection for Tests

When running in the `nix develop` environment, all required tools are automatically added to your PATH:
- `nc` (GNU netcat) with `-c` option support
- `curl` for HTTP requests
- `jq` for JSON processing
- `opencode` CLI tool

This ensures tests can reliably use `nc -l -p <port> -c '<command>'` for creating mock HTTP servers.

## Testing

The `tests/` directory contains comprehensive test suites for all components.

### Test Dependencies

Tests require the following dependencies (automatically provided in `nix develop`):

- **netcat-gnu**: Tests use GNU netcat's `-c` option for creating mock HTTP servers
- **curl**: For making HTTP requests to test APIs
- **jq**: For JSON processing and validation
- **bash**: POSIX-compatible shell features

### External Dependencies

Some tests may make requests to external services for integration testing:

**External Services Used:**
- Tests may use services like `httpbin.org` or similar for HTTP testing scenarios
- External site dependencies can cause flaky tests when services are unavailable
- Tests should gracefully handle external service failures with appropriate timeouts

**Test Stability Considerations:**
- **Mock-first approach**: Tests prefer internal mock servers using `nc -l -p <port> -c '<command>'` 
- **Graceful degradation**: External service failures should not cause complete test suite failures
- **Timeout configuration**: Network requests use conservative timeouts (30 seconds default)
- **Retry logic**: Critical tests may implement retry mechanisms for transient failures
- **Environment isolation**: Tests use temporary directories and clean up after themselves

**Dependency Requirements:**
- Mock servers are preferred over external dependencies where possible
- Network timeouts are configured to prevent hanging tests
- Tests that require external services should clearly document this dependency

### Running Tests

```bash
# Run all tests
./tests/test-orchestrator.sh
./tests/test-session-manager.sh
./tests/test-message.sh
./tests/test-multi-server.sh
./tests/test-error-handling.sh
./tests/test-template-integration.sh

# Tests use temporary directories and clean up after themselves
# Test logs are written to /tmp/opencode-*-test-$$/ directories
```

### Test Environment Notes

- Tests create temporary directories under `/tmp/` for isolation
- Mock HTTP servers use GNU netcat's `-c` option for command execution
- All tests are designed to be idempotent and safe to run multiple times
- Tests automatically find available ports to avoid conflicts

## Architecture

The multi-agent system follows these principles:

- **Session-based**: Each agent interaction is managed through sessions
- **Message-driven**: Agents communicate through structured JSON messages
- **Error-resilient**: Comprehensive error handling and recovery mechanisms
- **Load-balanced**: Support for multiple server instances with health checking

### Component Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   orchestrator  │    │ session-manager │    │    message.sh   │
│     .sh         │◄──►│      .sh        │◄──►│                 │
│                 │    │                 │    │ (API interface) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│multi-server-mgr │    │unified-error    │    │   OpenCode API  │
│      .sh        │    │  -handler.sh    │    │   (External)    │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Flow

1. **Session Management**: Sessions are stored in `${XDG_STATE_HOME}/opencode/sessions/<host_port>/<project>.session`
2. **Message Passing**: JSON messages flow through the `message.sh` interface to OpenCode API
3. **Error Handling**: All components use `unified-error-handler.sh` for consistent error reporting
4. **Load Balancing**: `multi-server-manager.sh` manages multiple OpenCode instances

### Testing Architecture

Tests use a multi-layered approach:
- **Unit Tests**: Test individual script functions in isolation
- **Integration Tests**: Test component interactions using mock servers
- **End-to-End Tests**: Full system tests using real or mock OpenCode instances

Mock HTTP servers are created using: `nc -l -p <port> -c '<response_command>'`

## Configuration

Session and state files are stored in:
```
${XDG_STATE_HOME:-$HOME/.local/state}/opencode/sessions/<host_port>/<project>.session
```

## Development Environment Verification

To verify your development environment is properly configured:

```bash
# Enter the development environment
cd ../../  # Go to opencode root directory
nix develop

# Verify all required tools are available
which nc curl jq opencode
nc --help | head -3  # Should show "GNU netcat"

# CRITICAL: Verify GNU netcat -c option support
if nc --help 2>&1 | grep -q "\-c"; then
    echo "✅ GNU netcat with -c option detected"
else
    echo "❌ ERROR: GNU netcat with -c option NOT found"
    echo "   This will cause test failures. Use 'nix develop' to get correct version."
fi

# Test basic functionality
curl --version
jq --version

# Return to template directory
cd templates/multi-agent

# Run a quick test to validate GNU netcat functionality
echo "Testing GNU netcat mock server capability..."
timeout 2 nc -l -p 9999 -c 'echo "HTTP/1.1 200 OK\r\n\r\nOK"' &
sleep 1
if curl -s http://localhost:9999 | grep -q "OK"; then
    echo "✅ GNU netcat mock server test PASSED"
else
    echo "❌ GNU netcat mock server test FAILED"
fi
```

**Expected output should show:**
- `nc` from `/nix/store/...netcat-gnu.../bin/nc`
- GNU netcat version 0.7.1 or newer with `-c` and `-e` options
- "✅ GNU netcat with -c option detected"
- "✅ GNU netcat mock server test PASSED"
- All test scripts should be executable and find their dependencies

**If you see errors:**
- Ensure you're in `nix develop` shell
- BSD netcat will show "netcat: invalid option -- 'c'" 
- macOS default netcat lacks `-c` option

## Contributing

When making changes:

1. Ensure all tests pass in the `nix develop` environment
2. Test with both single and multi-agent configurations  
3. Verify error handling and recovery scenarios
4. Update documentation for any new dependencies or requirements
5. Verify that GNU netcat `-c` option works for mock HTTP servers