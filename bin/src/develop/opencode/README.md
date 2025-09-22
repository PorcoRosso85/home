# OpenCode Flake

HTTP-only two-server OpenCode development environment with dynamic client capabilities and multi-agent templates.

## 🚀 High-Performance Usage (Recommended)

**Best for production use and frequent interactions.** Install once, use everywhere with optimal performance.

### One-Time Setup
```bash
# Install opencode-client to your profile (persistent across sessions)
nix profile install github:PorcoRosso85/home#opencode-client
```

### Daily Usage
```bash
# 1. Start server (in one terminal)
nix run nixpkgs#opencode -- serve --port 4096

# 2. Use installed client (instant startup)
OPENCODE_PROJECT_DIR=$(pwd) opencode-client 'just say hi'

# 3. Continue working (no startup delays)
OPENCODE_PROJECT_DIR=$(pwd) opencode-client 'explain this code'
OPENCODE_PROJECT_DIR=$(pwd) opencode-client 'add error handling'
```

**⚡ Performance Benefits:**
- **Zero startup time** - client launches instantly
- **Persistent across terminals** - works in any shell session
- **Memory efficient** - no repeated dependency resolution
- **Network optimized** - no repeated downloads

**🔧 Management Commands:**
```bash
# Update to latest version
nix profile upgrade github:PorcoRosso85/home#opencode-client

# Remove if needed
nix profile remove opencode-client

# Check installation
which opencode-client && echo "✅ Installed" || echo "❌ Not found"
```

## ⚡ 30-Second Quick Start (External Users)

**New to OpenCode? Get started immediately with the profile-based workflow:**

```bash
# Step 1: Install opencode-client (one-time setup)
nix profile install github:PorcoRosso85/home#opencode-client

# Step 2: Start server (in one terminal)
nix run nixpkgs#opencode -- serve --port 4096

# Step 3: Check status (in another terminal) - confirms URL and readiness
OPENCODE_PROJECT_DIR=$(pwd) opencode-client status

# Step 4: Send a message (same terminal)
OPENCODE_PROJECT_DIR=$(pwd) opencode-client 'just say hi'
```

**That's it!** The status check ensures everything is ready before you send your first message.

**🧪 Verify everything works:** Run our validation script:
```bash
./quick-start-test.sh
```

## 🔧 Troubleshooting

**Something not working?** Follow this progression:
```bash
# Step 1: Quick built-in check
OPENCODE_PROJECT_DIR=$(pwd) opencode-client status

# Step 2: If server connection fails, discover running servers
OPENCODE_PROJECT_DIR=$(pwd) opencode-client ps

# Step 3: Use the export command shown by ps, then verify
export OPENCODE_URL=http://127.0.0.1:PORT  # Copy from ps output
OPENCODE_PROJECT_DIR=$(pwd) opencode-client status --probe

# Step 4: If still issues, run comprehensive diagnostics
./check-opencode-status.sh
```

**📍 PATH Troubleshooting:** If `opencode-client` command is not found:

```bash
# Option 1: Install to profile (recommended for persistent use)
nix profile install github:PorcoRosso85/home#opencode-client

# Option 2: Use direct nix run (slower, for one-time use)
OPENCODE_PROJECT_DIR=$(pwd) nix run github:PorcoRosso85/home#opencode-client -- status
OPENCODE_PROJECT_DIR=$(pwd) nix run github:PorcoRosso85/home#opencode-client -- ps
OPENCODE_PROJECT_DIR=$(pwd) nix run github:PorcoRosso85/home#opencode-client -- status --probe
```

**🔍 New: Server Discovery** - The `ps` subcommand finds running OpenCode servers and provides exact export commands. **Note**: `ps` lists servers but does NOT automatically connect - you choose which server to use for predictable, auditable connections.

## 🎛️ Convenience Usage (One-time, No Install)

**For occasional use or when you can't install to profile.** ⚠️ **Performance Note**: Each command has startup overhead.

### Direct Commands (Slower)
```bash
# 1. Start server (in one terminal)
nix run nixpkgs#opencode -- serve --port 4096

# 2. Use client directly (slower startup each time)
OPENCODE_PROJECT_DIR=$(pwd) nix run github:PorcoRosso85/home#opencode-client -- 'just say hi'
OPENCODE_PROJECT_DIR=$(pwd) nix run github:PorcoRosso85/home#opencode-client -- status
OPENCODE_PROJECT_DIR=$(pwd) nix run github:PorcoRosso85/home#opencode-client -- ps
```

**⚠️ Performance Impact:**
- **3-5 second startup delay** per command
- **Network overhead** for dependency resolution
- **Memory inefficient** for repeated use
- **Best for**: One-off tasks, testing, systems where profile install isn't available

**💡 Migration Path:** If you find yourself using these commands regularly, consider upgrading to the High-Performance Usage approach:
```bash
# Upgrade to persistent installation
nix profile install github:PorcoRosso85/home#opencode-client
# Then use: opencode-client [command] (instant startup)
```

---

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

**📍 Key Requirement**: `OPENCODE_PROJECT_DIR` must be set to an existing directory.

**💡 Pro Tips:**
- Use `$(pwd)` for current directory: `OPENCODE_PROJECT_DIR=$(pwd)`
- Each directory gets its own conversation session
- Server must be running on port 4096 (default)

```bash
# ✅ Recommended: Use current directory
OPENCODE_PROJECT_DIR=$(pwd) \
  opencode-client 'just say hi'

# ✅ Alternative: Specific project directory
OPENCODE_PROJECT_DIR=/path/to/project \
  opencode-client 'just say hi'

# ✅ Backward compatibility (still works)
OPENCODE_PROJECT_DIR=$(pwd) \
  opencode-client 'just say hi'

# ✅ With specific provider/model (advanced)
OPENCODE_PROJECT_DIR=$(pwd) \
OPENCODE_PROVIDER=anthropic OPENCODE_MODEL=claude-3-5-sonnet \
  opencode-client 'explain quantum computing'
```

**🔧 Troubleshooting Quick Checks:**
```bash
# ⚡ All-in-one validation (recommended)
./quick-start-test.sh

# 🔍 Built-in diagnostics (lightweight)
OPENCODE_PROJECT_DIR=$(pwd) opencode-client status

# 🔍 Individual checks:
# Discover running OpenCode servers (new!)
OPENCODE_PROJECT_DIR=$(pwd) opencode-client ps

# Check if specific server is running
curl -s http://127.0.0.1:4096/doc >/dev/null && echo "✅ Server OK" || echo "❌ Server not running"

# Test with minimal setup
OPENCODE_PROJECT_DIR=$(pwd) opencode-client 'test message'

# Check detailed configuration status
./check-opencode-status.sh
```

**🔄 Directory-Based Session Continuity** (New Feature):
The built-in client manages session continuity based on the directory you specify via `OPENCODE_PROJECT_DIR`. Each directory maintains its own independent conversation session:

```bash
# Sessions are automatically saved and resumed per directory
OPENCODE_PROJECT_DIR=/path/to/project-a \
  opencode-client 'help with project A'  # Creates new session
OPENCODE_PROJECT_DIR=/path/to/project-a \
  opencode-client 'continue our discussion'  # Resumes same session

OPENCODE_PROJECT_DIR=/path/to/project-b \
  opencode-client 'different project here'  # Completely separate session
```

**Session Features:**
- **1x1 Directory Mapping**: Each project directory (from OPENCODE_PROJECT_DIR) gets its own unique session
- **Automatic Resumption**: Reuse the same OPENCODE_PROJECT_DIR to continue your previous conversation
- **Mandatory Directory Selection**: OPENCODE_PROJECT_DIR must be set and point to an existing directory (unset or missing paths cause an error)
- **Server Validation**: Invalid sessions result in clear error (no automatic recreation)
- **XDG Compliant**: Sessions stored in `${XDG_STATE_HOME:-$HOME/.local/state}/opencode/sessions/`
- **User Feedback**: Clear indication whether session was resumed or newly created
- **Operational Enhancement**: SID↔directory bidirectional mapping for diagnostics and cleanup

#### 📜 Conversation History and Session Management

**New in this version**: Enhanced client with conversation history retrieval and session management capabilities.

**View conversation history:**
```bash
# View history for current directory's session
OPENCODE_PROJECT_DIR=/path/to/project \
  opencode-client history

# View history for specific session
OPENCODE_PROJECT_DIR=/path/to/project \
  opencode-client history --sid ses_example123

# Get history in JSON format
OPENCODE_PROJECT_DIR=/path/to/project \
  opencode-client history --format json

# Limit number of messages
OPENCODE_PROJECT_DIR=/path/to/project \
  opencode-client history --limit 10
```

**Manage sessions:**
```bash
# List sessions for current directory
OPENCODE_PROJECT_DIR=/path/to/project \
  opencode-client sessions

# List sessions for different directory
opencode-client sessions --dir /other/project

# List all sessions for specific server
opencode-client sessions --hostport 127.0.0.1:4096

# Get session list in JSON format
OPENCODE_PROJECT_DIR=/path/to/project \
  opencode-client sessions --format json
```

**Complete workflow example:**
```bash
# 1. Send a message (creates session)
OPENCODE_PROJECT_DIR=/path/to/my-project \
  opencode-client "explain git branching"

# 2. Continue conversation
OPENCODE_PROJECT_DIR=/path/to/my-project \
  opencode-client "show me a practical example"

# 3. View conversation history
OPENCODE_PROJECT_DIR=/path/to/my-project \
  opencode-client history

# 4. List all sessions
OPENCODE_PROJECT_DIR=/path/to/my-project \
  opencode-client sessions
```

**Available commands:**
- `send [MESSAGE]` - Send message to current session (default behavior)
- `history [OPTIONS]` - View conversation history
- `sessions [OPTIONS]` - List available sessions
- `ps` - Discover running OpenCode servers (explicit URLs, no auto-connect)
- `status [--probe]` - Quick diagnostic check (--probe: test send capability)
- `help` - Show command usage

**🔍 ps Command Design Philosophy:**
The `ps` command follows explicit design principles for maximum predictability:
- **Lists servers** but **never automatically connects**
- **Shows exact export commands** for you to copy and execute
- **Prevents accidental connections** to wrong servers
- **Auditable and predictable** - you always know which server you're targeting

**Backward compatibility:** All existing commands continue to work unchanged. The new ps and enhanced status features are additive.

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
OPENCODE_PROJECT_DIR=/path/to/project \
  opencode-client 'just say hi'

# Environment variables for testing
export OPENCODE_URL="http://127.0.0.1:4096"
export OPENCODE_PROVIDER="anthropic"
export OPENCODE_MODEL="claude-3-5-sonnet"
```

---

## 🤔 Which Approach Should I Use?

| **Your Goal** | **Recommended Approach** |
|---------------|-------------------------|
| **Regular OpenCode usage** | **High-Performance Usage** (profile install) |
| **Quick testing or evaluation** | **30-Second Quick Start** |
| **One-off tasks or restricted environments** | **Convenience Usage** |
| **Template development and testing** | **Development Usage** |
| **Learning the HTTP API directly** | **Direct HTTP API Usage** |
| **Contributing to OpenCode templates** | **Development Usage** |
| **Multi-agent system development** | **Development Usage** |

## 📦 Migration Guide for Existing Users

**Upgrading from manual nix run commands?** Here's your migration path:

### Before (Slow)
```bash
# Old way - startup delay every time
OPENCODE_PROJECT_DIR=$(pwd) nix run .#opencode-client -- 'message'
OPENCODE_PROJECT_DIR=$(pwd) nix run .#opencode-client -- status
```

### After (Fast)
```bash
# 1. One-time upgrade
nix profile install github:PorcoRosso85/home#opencode-client

# 2. New way - instant startup
OPENCODE_PROJECT_DIR=$(pwd) opencode-client 'message'
OPENCODE_PROJECT_DIR=$(pwd) opencode-client status
```

**🔄 All your existing workflows remain compatible** - just replace the `nix run` prefix with the installed `opencode-client` command.

**📍 Local Development**: If you're working on the OpenCode codebase itself, you can still use `nix run .#opencode-client` for testing local changes.

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

# Required for client
export OPENCODE_PROJECT_DIR="/path/to/project"     # Project directory (required)

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
OPENCODE_PROJECT_DIR=$(pwd) OPENCODE_URL=$OPENCODE_URL_A opencode-client 'test with server A'
OPENCODE_PROJECT_DIR=$(pwd) OPENCODE_URL=$OPENCODE_URL_B opencode-client 'test with server B'
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

### 🔍 TUI vs HTTP API Configuration Differences

**Important**: The TUI and HTTP API may show different provider/model information:

**Configuration Priority** (highest to lowest):
1. **TUI Settings** - Set via TUI interface (takes precedence)
2. **Environment Variables** - `OPENCODE_PROVIDER`, `OPENCODE_MODEL`
3. **Config Files** - `~/.config/opencode/opencode.json` or `./opencode.json`
4. **Server Defaults** - Fallback when no other config

**Common Scenarios**:
```bash
# Scenario 1: TUI shows different models than HTTP API
curl -s $OPENCODE_URL/config/providers | jq '.providers[].id'  # May show 'opencode' only
# But actual model responds as 'anthropic/claude-sonnet-4'

# Scenario 2: Check what model actually responds (regardless of API display)
SID=$(curl -s -X POST $OPENCODE_URL/session -H 'Content-Type: application/json' -d '{}' | jq -r .id)
curl -s -X POST $OPENCODE_URL/session/$SID/message \
  -H 'Content-Type: application/json' \
  -d '{"parts":[{"type":"text","text":"What model are you?"}],"model":{"providerID":"opencode","modelID":"grok-code"}}' | jq -r '.parts[0].text'
# May return anthropic model name even when requesting opencode/grok-code
```

**Troubleshooting**: If HTTP API shows limited providers but TUI has more configured, this is normal behavior. The TUI configuration takes precedence for actual model usage.

**🔧 Detailed Troubleshooting**: For comprehensive troubleshooting guidance and diagnostic tools, see:
- `./check-opencode-status.sh` - Diagnostic script for configuration analysis
- `docs/TROUBLESHOOTING-TUI-HTTP-API.md` - Complete troubleshooting guide

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
OPENCODE_PROJECT_DIR=$(pwd) opencode-client 'test message'
```

### Test Development Usage  
```bash
# Enter development environment
nix develop

# Verify all tools are available
which nc curl jq opencode-client

# Verify GNU netcat (critical for template tests)
nc --help | head -3  # Should show "GNU netcat"

# Test template functionality
cd templates/multi-agent
./tests/test-session-manager.sh
```

## 🤖 CI/Ephemeral Environment Note

**For specialized use cases only** - CI pipelines, containers, or environments where profile persistence isn't suitable.

**⚠️ Important**: Regular usage should use the [High-Performance Usage](#-high-performance-usage-recommended) approach with profile install. This section is for scenarios where profiles can't be used.

### One-Shot Execution
```bash
# Start server and run single command (no persistent state)
nix shell github:PorcoRosso85/home#opencode-client -c opencode-client status

# With environment variables for CI
OPENCODE_PROJECT_DIR=/workspace \
OPENCODE_URL=http://127.0.0.1:4096 \
  nix shell github:PorcoRosso85/home#opencode-client -c opencode-client 'analyze code'

# Multiple commands in CI context
OPENCODE_PROJECT_DIR=/workspace \
  nix shell github:PorcoRosso85/home#opencode-client -c opencode-client ps
OPENCODE_PROJECT_DIR=/workspace \
  nix shell github:PorcoRosso85/home#opencode-client -c opencode-client 'run tests'
```

**Performance Note**: Each `nix shell` invocation has 3-5 second startup overhead. For any interactive or repeated usage, install to profile instead.

## 📚 More Information

- **Template Documentation:** See `templates/*/README.md` for detailed template usage
- **API Reference:** Start a server and visit `http://127.0.0.1:4096/doc` for OpenAPI documentation
- **Multi-Agent Details:** See `templates/multi-agent/README.md` for comprehensive multi-agent system documentation

---

**Remember:** Choose **Basic Usage** for quick API work, **Development Usage** for template development and testing!