# OpenCode Development Guidelines for AI Agents

## Build/Test Commands
```bash
# Run all tests in tests/ directory
bash tests/session_continuity_test.sh
bash tests/flake_compliance_test.sh

# Run a single test file
bash test-flake-description.sh

# Test multi-agent templates (requires nix develop)
nix develop
cd templates/multi-agent && ./tests/test-orchestrator.sh
```

## Code Style Guidelines
- **Shell Scripts**: Use `#!/usr/bin/env bash` and `set -euo pipefail` for safety
- **Error Handling**: Always use explicit error checking; fail early with clear messages
- **Functions**: Prefix with context (e.g., `oc_session_*` for session functions)
- **Variables**: Use `readonly` for constants, `local` in functions, UPPERCASE for exports
- **Dependencies**: Source shared functions from `lib/` directory (e.g., `source lib/session-helper.sh`)
- **Testing**: Write self-contained tests with mock servers when possible
- **Nix**: Keep flake.nix minimal; extract shell logic to separate `.sh` files in `lib/`