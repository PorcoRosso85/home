# flake-dependency POC

## Purpose
Single-responsibility POC for analyzing flake dependencies using a lock-first approach.

## Scope and Responsibilities

### In Scope (This Flake's Responsibility)
- ✅ `lib.deps.index`: List dependencies from flake.lock (lock-first approach)
- ✅ Schema v2 dependency structure with locked/original information
- ✅ Follows resolution for indirect dependencies
- ✅ Skip inputs functionality for filtering

### Out of Scope (NOT This Flake's Responsibility)
- ❌ Documentation collection → See `poc/flake-readme`
- ❌ readme.nix processing → See `poc/flake-readme`
- ❌ Combined docs+deps functionality (removed for single responsibility)
- ❌ Cross-flake documentation collection

## Main Functionality

### Dependency Analysis
```bash
# Analyze flake dependencies from lock file
nix build .#deps-json && jq '.deps' result
```

### Core Module
- `lib/core-indexer.nix`: Dependency indexing with lock-first approach

## Implementation Status

### ✅ Completed Features (Schema v2)
- [x] `lib.deps.index`: **lock-first, flake.lock required (Schema v2)**
- [x] `packages.deps-json`: CI/CD JSON output with timestamp
- [x] **Performance improvement**: ~10x faster with no evaluation overhead
- [x] flake-parts modularization
- [x] Skip inputs functionality for filtering dependencies

### 🔧 Future Improvements
- [ ] CI gates with checks integration
- [ ] Transitive dependencies support (depth > 1)
- [ ] Enhanced filtering options

## Directory Structure
```
.
├── README.md               # This file
├── readme.nix             # Root responsibility definition
├── flake.nix              # flake-parts configuration
├── flake.lock             # Dependency lock file
├── lib/
│   └── core-indexer.nix  # Core dependency indexing logic
└── test-deps-structure.sh  # Test script
```

## Usage Examples

### 1. Generate Dependency JSON
```bash
nix build .#deps-json
cat result | jq .
```

### 2. Run Tests
```bash
./test-deps-structure.sh
```

### 3. Direct Function Calls (Development)
```bash
# Dependency analysis only
nix eval --json '.#packages.x86_64-linux.deps-json' | jq '.deps'
```

## Acceptance Criteria Status (Schema v2)

- ✅ `lib.deps.index` lists dependencies efficiently (lock-first, flake.lock required)
- ✅ `nix build .#deps-json` returns `{schemaVersion=2, deps, generatedAt}`
- ✅ generatedAt in real-time ISO 8601 format
- ✅ All tests pass (`./test-deps-structure.sh`)

## Composing with flake-readme

For projects needing both dependency analysis and documentation collection:

```nix
{
  inputs = {
    flake-dependency.url = "path:../poc/flake-dependency";
    flake-readme.url = "path:../poc/flake-readme";
  };

  outputs = { flake-dependency, flake-readme, ... }: {
    # Use each POC for its single responsibility
    myDeps = flake-dependency.lib.deps.index { 
      lockPath = ./flake.lock; 
    };
    myDocs = flake-readme.lib.docs.index { 
      root = ./.; 
    };
  };
}
```

## Basic Usage

```bash
# Build the dependency index
nix build .#deps-json

# View the output
cat result | jq
```

### Library Functions (requires lockPath)
```bash
# Direct evaluation with lockPath
nix eval --json .#lib.deps.index --apply 'f: f { lockPath = toString ./flake.lock; }' | jq
```

Note: lockPath is a required parameter with no fallback. This ensures environmental stability and reproducible builds.

## Using from External Flakes

The lib functions are exposed at the flake level for external use:

### flake.nix setup
```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-dependency.url = "github:yourusername/flake-dependency";
    # ... other inputs
  };

  outputs = { self, nixpkgs, flake-dependency, ... }:
    let
      system = "x86_64-linux";  # or your target system
      pkgs = nixpkgs.legacyPackages.${system};
    in {
      # Use the lib functions
      myDeps = flake-dependency.lib.deps.index { 
        lockPath = ./flake.lock; 
      };
    };
}
```

### Available functions

- **`lib.deps.index`**: Analyze flake dependencies from lock file
  ```nix
  # Parameters: { lockPath?, lockData?, skipInputs?, depth? }
  deps.index { lockPath = ./flake.lock; }
  ```

### Usage examples

```bash
# Test external usage (impure evaluation required for file access)
nix eval --impure path/to/external/flake#myDeps --json
```

The functions are system-independent and work with either `lockPath` or `lockData` parameters.
