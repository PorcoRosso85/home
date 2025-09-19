# OpenCode Flake

HTTP-only two-server OpenCode development environment with dynamic client capabilities and multi-agent templates.

## 🎯 Which Flake to Use?

**Default:** Use `flake.nix` for all standard usage - it's the unified, single entry point.

**Alternatives:** Alternative implementations available in `examples/` directory for reference:
- `examples/flake-core.nix` - Minimal core HTTP client only
- `examples/flake-enhanced.nix` - Configuration-based feature switching

## 🚀 Choose Your Usage Approach

**There are two distinct ways to use OpenCode - choose based on your needs:**

### 🚀 Basic Usage (No `nix develop` needed)

**Use this when:** You want to quickly interact with OpenCode servers or use the HTTP API directly.

**What you get:** Direct access to OpenCode server and HTTP client functionality.

**No setup required** - just run the commands below:

#### Start a Server
```bash
# Start OpenCode server (requires existing nixpkgs with opencode)
nix run nixpkgs#opencode -- serve --port 4096
```

#### Use the Built-in Client
```bash
# Quick test with built-in client (unified command)
nix run .#opencode-client -- 'just say hi'

# Backward compatibility (still works)
nix run .#client-hello -- 'just say hi'

# With specific provider/model
OPENCODE_PROVIDER=anthropic OPENCODE_MODEL=claude-3-5-sonnet \
  nix run .#opencode-client -- 'explain quantum computing'
```

**🔄 Directory-Based Session Continuity** (New Feature):
The built-in client now automatically manages session continuity based on your working directory. Each directory maintains its own independent conversation session:

```bash
# Sessions are automatically saved and resumed per directory
cd /path/to/project-a
nix run .#opencode-client -- 'help with project A'  # Creates new session
nix run .#opencode-client -- 'continue our discussion'  # Resumes same session

cd /path/to/project-b  
nix run .#opencode-client -- 'different project here'  # Completely separate session
```

**Session Features:**
- **1x1 Directory Mapping**: Each working directory gets its own unique session
- **Automatic Resumption**: Return to any directory to continue your previous conversation
- **Flexible Directory Selection**: Uses `OPENCODE_PROJECT_DIR` if set, otherwise current working directory
- **Server Validation**: Invalid sessions are automatically recreated
- **XDG Compliant**: Sessions stored in `${XDG_STATE_HOME:-$HOME/.local/state}/opencode/sessions/`
- **User Feedback**: Clear indication whether session was resumed or newly created

#### Direct HTTP API Usage

**Session Management Model:**
Sessions are server-managed conversation state. The client holds only a session ID for reference, while all conversation history and context is maintained server-side.

**API Flow Pattern:**
1. `POST /session` → Receive session ID from server
2. `POST /session/:id/message` → Send messages using the session ID reference
3. Session not found (404) → Recreate session and get new ID

```bash
# Step 1: Create a session (server creates state, returns ID reference)
SID=$(curl -s -X POST http://127.0.0.1:4096/session \
  -H 'Content-Type: application/json' \
  -d '{}' | jq -r .id)

# Step 2: Send messages (client references server-side state via ID)
curl -s -X POST http://127.0.0.1:4096/session/$SID/message \
  -H 'Content-Type: application/json' \
  -d '{"parts":[{"type":"text","text":"hi"}]}'

# Step 3: Continue conversation (same session ID references server state)
curl -s -X POST http://127.0.0.1:4096/session/$SID/message \
  -H 'Content-Type: application/json' \
  -d '{
    "parts":[{"type":"text","text":"explain AI"}],
    "model":{"providerID":"anthropic","modelID":"claude-3-5-sonnet"}
  }'
```

---

### 🛠️ Development Usage (`nix develop` recommended)

**Use this when:** You want to develop with templates, run tests, or create multi-agent systems.

**What you get:** Full development environment with curl, jq, GNU netcat, and all testing tools.

**Setup required** - enter the development environment:

```bash
# Enter development environment
nix develop

# Now you have access to all development tools:
# - opencode CLI
# - curl (HTTP client)
# - jq (JSON processor)  
# - nc (GNU netcat with -c option for testing)
```

#### Template Development
```bash
# After 'nix develop', create projects from templates:

# Simple HTTP client template
nix flake init -t .#opencode-client

# Multi-agent system template (requires GNU netcat)
nix flake init -t .#multi-agent
```

#### Running Template Tests
```bash
# Multi-agent template tests (requires 'nix develop' environment)
cd templates/multi-agent/
./tests/test-orchestrator.sh
./tests/test-session-manager.sh
./tests/test-message.sh
```

#### Built-in Client Development Testing
```bash
# Test the client with development environment
nix run .#client-hello -- 'just say hi'

# Environment variables for testing
export OPENCODE_URL="http://127.0.0.1:4096"
export OPENCODE_PROVIDER="anthropic"
export OPENCODE_MODEL="claude-3-5-sonnet"
```

---

## 🤔 Which Approach Should I Use?

| **Your Goal** | **Recommended Approach** |
|---------------|-------------------------|
| Quick API testing or one-off requests | **Basic Usage** |
| Integrating OpenCode into existing scripts | **Basic Usage** |
| Learning the HTTP API | **Basic Usage** |
| Developing multi-agent systems | **Development Usage** |
| Running template tests | **Development Usage** |
| Contributing to OpenCode templates | **Development Usage** |
| Using GNU netcat for testing | **Development Usage** |

## 📋 Available Templates

When using **Development Usage** (`nix develop`), you get access to these templates:

### opencode-client
- **Purpose:** Dynamic HTTP client template (pre-auth assumed)
- **Usage:** `nix flake init -t .#opencode-client`
- **Dependencies:** curl, jq (auto-provided in dev environment)

### multi-agent  
- **Purpose:** Session/message/orchestrator system
- **Usage:** `nix flake init -t .#multi-agent`
- **Dependencies:** curl, jq, **GNU netcat** (auto-provided in dev environment)
- **⚠️ Important:** Requires GNU netcat with `-c` option - automatically provided in `nix develop`

## 🔧 Environment Variables

Both usage approaches support these environment variables:

```bash
# Server connection
export OPENCODE_URL="http://127.0.0.1:4096"        # Default server URL

# Provider/model selection (optional - server defaults used if omitted)
export OPENCODE_PROVIDER="anthropic"               # AI provider
export OPENCODE_MODEL="claude-3-5-sonnet"          # Specific model

# Development/testing (Development Usage only)
export XDG_STATE_HOME="$HOME/.local/state"         # Session storage
export OPENCODE_TIMEOUT="30"                       # API timeout in seconds
export OPENCODE_PROJECT="my-project"               # Project name
```

## 🔧 Operational Guidelines

### Server Management

**⚠️ Avoid multiple servers with same provider**: Don't run multiple Claude or GPT servers simultaneously on the same machine. This can lead to:
- API rate limiting conflicts
- Inconsistent model responses  
- Resource contention and poor performance
- Difficulty tracking which server is responding

**🔄 Use fixed URLs for A/B server setup**: When testing different configurations or models, set up dedicated environment variables:
```bash
# A/B testing setup
export OPENCODE_URL_A="http://127.0.0.1:4096"     # Server A (e.g., Claude)
export OPENCODE_URL_B="http://127.0.0.1:4097"     # Server B (e.g., GPT)

# Switch between servers explicitly
OPENCODE_URL=$OPENCODE_URL_A nix run .#client-hello -- 'test with server A'
OPENCODE_URL=$OPENCODE_URL_B nix run .#client-hello -- 'test with server B'
```

**📍 Port management guidelines**:
- Use consistent ports: 4096 (primary), 4097 (secondary), 4098+ (testing)
- Document active servers: `ps aux | grep opencode` to see running instances
- Clean shutdown: Always use `Ctrl+C` or proper process termination

### Provider Verification

Before starting work, verify your server configuration to avoid confusion:

```bash
# Check current server provider and available models
curl -s $OPENCODE_URL/config/providers | jq '.default, .providers[].id'

# Verify server is responding
curl -s $OPENCODE_URL/health || echo "Server not responding at $OPENCODE_URL"

# Check what's running on common ports
netstat -tuln | grep -E ":(4096|4097|4098)\s"
```

**🔍 Quick provider identification**:
```bash
# Create a test session to see which model responds
SID=$(curl -s -X POST $OPENCODE_URL/session -H 'Content-Type: application/json' -d '{}' | jq -r .id)
curl -s -X POST $OPENCODE_URL/session/$SID/message \
  -H 'Content-Type: application/json' \
  -d '{"parts":[{"type":"text","text":"What AI model are you?"}]}' | jq -r '.parts[0].text'
```

### Best Practices

- **🚀 Single server workflow**: Start one server, use it consistently, shut it down cleanly
- **📝 Document your setup**: Note which ports and providers you're using
- **🧪 Test before switching**: Verify server responds before changing OPENCODE_URL
- **🔄 Clean restarts**: If switching providers, restart the server rather than reconfiguring

## 🚨 Common Misconceptions

**❌ MYTH:** "You always need `nix develop` to use OpenCode"  
**✅ TRUTH:** `nix develop` is only needed for template development and testing

**❌ MYTH:** "Basic HTTP API usage requires the development environment"  
**✅ TRUTH:** You can use curl and the HTTP API directly without any special setup

**❌ MYTH:** "All OpenCode functionality requires the full development shell"  
**✅ TRUTH:** Many use cases work perfectly with just `nix run` commands

## 🧪 Testing Your Setup

### Test Basic Usage (No nix develop)
```bash
# This should work without any special setup:
nix run .#client-hello -- 'test message'
```

### Test Development Usage  
```bash
# Enter development environment
nix develop

# Verify all tools are available
which nc curl jq opencode

# Verify GNU netcat (critical for template tests)
nc --help | head -3  # Should show "GNU netcat"

# Test template functionality
cd templates/multi-agent
./tests/test-session-manager.sh
```

## 📚 More Information

- **Template Documentation:** See `templates/*/README.md` for detailed template usage
- **API Reference:** Start a server and visit `http://127.0.0.1:4096/doc` for OpenAPI documentation  
- **Multi-Agent Details:** See `templates/multi-agent/README.md` for comprehensive multi-agent system documentation

---

**Remember:** Choose **Basic Usage** for quick API work, **Development Usage** for template development and testing!