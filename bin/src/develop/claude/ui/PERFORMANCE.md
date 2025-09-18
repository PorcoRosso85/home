# Performance Comparison

## Startup Time Comparison

| Method | Cold Start | Warm Start | File Access | Notes |
|--------|------------|------------|-------------|-------|
| `./claude-shell.sh` | ~0.3s | **0.1s** | ~50 files | ✅ Recommended - Fastest |
| `nix run .#core` | ~12s | 0.3s | 1000+ files | Good for distribution |
| `nix shell .#core -c ...` | ~3s | 2.5s | 1000+ files | Builds entire package |
| `nix develop -c ...` | ~1s | 0.8s | Minimal | Development environment |

## Why the Differences?

### `./claude-shell.sh` (Fastest)
- Uses `nix shell` with specific packages only
- No flake evaluation or package building
- Direct execution of scripts

### `nix run .#core` (Standard)
- Evaluates entire flake
- Builds packages if needed
- Provides proper isolation

### `nix shell .#core -c`
- Similar to `nix run` but less optimized
- Still builds the entire package
- Not recommended for frequent use

## Recommendations

1. **For daily use**: `./claude-shell.sh`
2. **For distribution**: `nix run .#core`
3. **For development**: `nix develop` then direct script execution

## Technical Details

The performance difference comes from:
- **File access patterns**: nix shell with individual packages avoids scanning the entire monorepo
- **Build requirements**: Direct script execution skips the Nix build phase
- **Caching behavior**: Simple package references are cached more efficiently