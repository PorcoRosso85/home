# OpenCode Client

Simple HTTP client for OpenCode AI assistant with session management.

## Quick Start

```bash
# Install once
nix profile install github:PorcoRosso85/home#opencode-client

# Use anywhere
OPENCODE_PROJECT_DIR=$(pwd) opencode-client 'your message here'
```

## Help & Documentation

- **Client help**: `opencode-client help`
- **OpenCode help**: `nix run nixpkgs#opencode -- --help`
- **API documentation**: Visit `http://server:port/doc` when server is running
- **Templates**: `nix develop` then explore `templates/` directory

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `OPENCODE_PROJECT_DIR` | Project directory (required) | current directory |
| `OPENCODE_URL` | Server URL | `http://127.0.0.1:4096` |

## Troubleshooting

1. **Server not found**: `opencode-client ps` to discover running servers
2. **Connection issues**: `opencode-client status --probe` for diagnostics
3. **Command not found**: Install with `nix profile install github:PorcoRosso85/home#opencode-client`

For detailed usage and options, run `opencode-client help`.