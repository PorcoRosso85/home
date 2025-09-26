# OpenCode Client

Simple HTTP client for OpenCode AI assistant with session management.

## 🏗️ Architecture Patterns

詳細は [`readme.nix`](./readme.nix) の `meta.patterns` を参照してください。

## Quick Start

```bash
# Install once
nix profile install github:PorcoRosso85/home#opencode-client

# Use anywhere (synchronous - wait for response)
OPENCODE_PROJECT_DIR=$(pwd) opencode-client 'your message here'

# Asynchronous mode (send and return immediately)
OPENCODE_PROJECT_DIR=$(pwd) opencode-client send --no-wait 'your message here'
```

## Help & Documentation

- **Client help**: `opencode-client help`
- **OpenCode help**: `nix run nixpkgs#opencode -- --help`
- **API documentation**: Visit `http://server:port/doc` when server is running
- **Templates**: `nix develop` then explore `templates/` directory
- **Git policy**: See [`.opencode/gitignore-policy.md`](.opencode/gitignore-policy.md) for artifact management
- **Quality verification**: `./.opencode/verify-basic.sh` を実行してください

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `OPENCODE_PROJECT_DIR` | Project directory (required) | current directory |
| `OPENCODE_URL` | Server URL | `http://127.0.0.1:4096` |

## Async Mode (--no-wait)

The `--no-wait` flag allows sending messages without waiting for responses, enabling async workflows:

- **Success**: Returns immediately with session ID and `[Next]` guidance
- **Error handling**: Exit code determines success/failure (not stderr content)
- **SSOT**: Use session history API to retrieve responses later

### Error Determination

The client determines success/failure by **exit code only**, not stderr content:
- **Exit 0**: Success (even if stderr contains warnings like Nix messages)
- **Exit 1**: Failure (structured error messages provided)
- **stderr vs stdout**: stderr contains metadata and warnings; stdout contains AI responses

## Nixpkgs Input Options

This flake uses fixed revision (`?rev=`) for maximum reproducibility. Alternative approaches:

| Input Type | Example | Benefits | Tradeoffs |
|------------|---------|----------|-----------|
| **Fixed revision** (current) | `?rev=8eaee110344796db060382e15d3af0a9fc396e0e` | 🔒 Ironclad reproducibility<br>✅ CI guarantees same build | ⚠️ No automatic security updates<br>📅 Manual revision updates required |
| **Stable branch** | `?ref=nixos-24.11` | 🛡️ Security updates included<br>📈 Stable feature progression | ⚠️ Builds may change over time<br>🔄 Requires CI monitoring |
| **Unstable branch** | `?ref=nixos-unstable` | 🚀 Latest OpenCode features<br>⚡ Fast bug fixes | ⚠️ Potential breaking changes<br>🧪 Requires extensive CI |

**Recommendation**: Keep fixed revision for production/teams. Consider stable branch for personal development with CI monitoring.

## Troubleshooting

1. **Server not found**: `opencode-client ps` to discover running servers
2. **Connection issues**: `opencode-client status --probe` for diagnostics
3. **Command not found**: Install with `nix profile install github:PorcoRosso85/home#opencode-client`
4. **OpenCode serve unavailable**:
   - **Recommended**: Use this flake's pinned version: `nix develop --command opencode serve --port 4096`
   - **Alternative**: Use flake inputs: `nix run --inputs-from . nixpkgs#opencode -- serve --port 4096`
5. **PATH conflicts with old opencode**:
   - Check which opencode: `command -v opencode`
   - Verify serve availability: `opencode --help | grep -i serve`
   - Remove old versions: `nix profile list | grep -i opencode` then `nix profile remove <INDEX>`

For detailed usage and options, run `opencode-client help`.

For advanced troubleshooting, see [docs/TROUBLESHOOTING-TUI-HTTP-API.md](docs/TROUBLESHOOTING-TUI-HTTP-API.md)

## Uninstall

To remove the client from your Nix profile:

```bash
# Check installation list
nix profile list

# Remove by index (safer than name)
nix profile remove <INDEX>
```

Replace `<INDEX>` with the index number shown in the `nix profile list` output for opencode-client.