# OpenCode TUI vs HTTP API Troubleshooting Guide

## Overview

This guide addresses the behavioral differences between OpenCode's TUI (Terminal User Interface) and HTTP API interfaces, helping developers understand and troubleshoot configuration-related issues.

## Key Principle: TUI Configuration Precedence

**Critical Understanding**: The TUI configuration always takes precedence over HTTP API configuration display. This means:

- What you see in HTTP API endpoints may not reflect the actual model being used
- TUI settings override environment variables, config files, and server defaults
- Authentication configured via TUI persists regardless of HTTP API display

## Configuration Priority Order

1. **TUI Settings** (Highest precedence)
2. **Environment Variables** (`OPENCODE_PROVIDER`, `OPENCODE_MODEL`)
3. **Config Files** (`~/.config/opencode/opencode.json`, `./opencode.json`, `$OPENCODE_CONFIG`)
4. **Server Defaults** (Lowest precedence)

## Common Issues and Solutions

### Issue 1: HTTP API Shows Limited Providers but TUI Works with Anthropic

**Symptoms:**
- `curl $OPENCODE_URL/config/providers` shows only "opencode" provider
- TUI successfully uses Anthropic models
- API requests with anthropic models work despite provider display

**Explanation:**
This is expected behavior. TUI configuration takes precedence over HTTP API display.

**Solution:**
✅ **This is not a problem** - Continue using the TUI-configured models

**Verification:**
```bash
# Test actual model functionality (not provider display)
./check-opencode-status.sh
```

### Issue 2: Environment Variables Don't Seem to Work

**Symptoms:**
- Set `OPENCODE_PROVIDER=anthropic` and `OPENCODE_MODEL=claude-sonnet-4`
- HTTP API still shows different providers
- Models don't behave as expected

**Root Cause:**
TUI configuration overrides environment variables.

**Solutions:**

**Option A: Use TUI Configuration (Recommended)**
1. Configure providers directly in TUI
2. Authentication persists across sessions
3. Most reliable method

**Option B: Reset TUI Configuration**
1. Clear TUI configuration to fall back to environment variables
2. Restart OpenCode server
3. Environment variables will then take effect

**Option C: Use Config Files**
```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "anthropic/claude-sonnet-4-20250514",
  "provider": {
    "anthropic": {
      "options": {
        "apiKey": "{env:ANTHROPIC_API_KEY}"
      }
    }
  }
}
```

### Issue 3: Model Name Mismatches

**Symptoms:**
- Request with specific model name returns different model
- HTTP API accepts model names not shown in provider list

**Example:**
```bash
# Request claude-opus-4-1-20250805
curl -X POST $OPENCODE_URL/session/$SID/message \
  -d '{"model":{"providerID":"anthropic","modelID":"claude-opus-4-1-20250805"}}'

# Actual response: claude-sonnet-4-20250514 behavior
```

**Explanation:**
TUI model configuration overrides the API request model specification.

**Solution:**
Use the diagnostic script to identify actual model:
```bash
./check-opencode-status.sh --format json | jq .server.actual_model_response
```

### Issue 4: Authentication Confusion

**Symptoms:**
- API key environment variables set but models don't work
- Confusion about which authentication method is active

**Troubleshooting Steps:**

1. **Check TUI Authentication Status:**
   ```bash
   # TUI should show authentication status
   opencode  # Start TUI and check provider status
   ```

2. **Verify Active Configuration:**
   ```bash
   ./check-opencode-status.sh
   ```

3. **Test Model Access:**
   ```bash
   # Create session and test model
   SID=$(curl -s -X POST $OPENCODE_URL/session -H 'Content-Type: application/json' -d '{}' | jq -r .id)
   curl -X POST $OPENCODE_URL/session/$SID/message \
     -H 'Content-Type: application/json' \
     -d '{"parts":[{"type":"text","text":"What model are you?"}]}'
   ```

## Diagnostic Procedures

### Quick Status Check

```bash
# Run comprehensive diagnostic
./check-opencode-status.sh

# JSON output for scripting
./check-opencode-status.sh --format json
```

### Manual Server Configuration Check

```bash
# Check what HTTP API reports
curl -s $OPENCODE_URL/config/providers | jq

# Check server health
curl -s $OPENCODE_URL/health

# Test actual model response
SID=$(curl -s -X POST $OPENCODE_URL/session -d '{}' | jq -r .id)
curl -s -X POST $OPENCODE_URL/session/$SID/message \
  -H 'Content-Type: application/json' \
  -d '{"parts":[{"type":"text","text":"What AI model are you?"}]}' | jq
```

### Environment Analysis

```bash
# Check OpenCode-related environment variables
env | grep -E '^OPENCODE_|^ANTHROPIC_|^OPENAI_'

# Check configuration files
ls -la ~/.config/opencode/
ls -la ./opencode.json
```

## Expected Behavior Patterns

### Normal TUI + HTTP API Operation

1. **TUI Configuration Present:**
   - HTTP API may show limited providers
   - TUI-configured models work correctly
   - API requests use TUI models regardless of request specification

2. **No TUI Configuration:**
   - HTTP API reflects actual provider configuration
   - Environment variables and config files take effect
   - API requests honor model specifications

### Troubleshooting Decision Tree

```
Is the server responding to API calls?
├── No → Check server status, restart if needed
└── Yes → Are models working as expected?
    ├── Yes → Configuration difference is normal behavior
    └── No → Check authentication and model availability
        ├── TUI configured? → Use TUI configuration
        └── No TUI config → Check env vars and config files
```

## Best Practices

### For Development

1. **Use TUI for primary configuration**
   - Most reliable authentication method
   - Persistent across sessions
   - Overrides other configuration sources

2. **Use HTTP API for programmatic access**
   - Don't rely on provider display for configuration
   - Test actual functionality, not configuration display
   - Use diagnostic script for verification

3. **Documentation and sharing**
   - Include actual model responses in tests
   - Don't assume HTTP API provider list reflects reality
   - Use diagnostic tools for status verification

### For CI/CD and Automation

1. **Environment-based configuration**
   - Clear TUI configuration for automation
   - Use config files for reproducible setups
   - Test actual functionality in pipelines

2. **Verification steps**
   - Run diagnostic script in CI
   - Test model responses, not provider configuration
   - Include authentication verification

## Related Documentation

- **README.md**: Main usage guide with configuration differences section
- **check-opencode-status.sh**: Diagnostic script for status verification
- **OpenCode Config Documentation**: https://opencode.ai/docs/config/
- **OpenCode Server API**: See `docs/2025-09-20_20-33-37_opencode.ai_server.md`

## Support and Further Help

If you encounter issues not covered in this guide:

1. Run the diagnostic script: `./check-opencode-status.sh`
2. Check the main README.md for configuration examples
3. Verify server and TUI status independently
4. Test actual model functionality rather than configuration display

Remember: **TUI configuration precedence is by design**, not a bug. Understanding this principle resolves most configuration confusion.