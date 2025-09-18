# Requirement Coverage Analysis

Analyzes differences between requirements (KuzuDB) and implementation (filesystem).

## Usage
```bash
nix run .                                    # Show this README
nix run . -- analyze /path                   # Analyze coverage
nix run . -- analyze /path --show-symbols    # With symbols
nix run . -- analyze req_only /path          # Requirements only
nix run . -- analyze impl_only /path         # Implementation only
```

## Output
```json
{
  "path": "/file",
  "requirement_exists": true,
  "implementation_exists": false
}
```