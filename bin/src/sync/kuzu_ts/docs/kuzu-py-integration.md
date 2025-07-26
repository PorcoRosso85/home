# KuzuDB Python Environment Integration

## Overview

This document describes how to integrate kuzu-py's Python environment into sync/kuzu_ts.

## Current Implementation

The sync/kuzu_ts flake now uses kuzu-py as a dependency:

```nix
inputs = {
  kuzu-py.url = "path:../../persistence/kuzu_py";
};

pythonEnv = pkgs.python312.withPackages (ps: with ps; [
  # kuzu-pyからのパッケージ
  kuzu-py.packages.${system}.kuzuPy
  # 既存のテスト用パッケージ
  pytest
  pytest-asyncio
  websockets
  httpx
]);
```

## Benefits

1. **Unified KuzuDB Implementation**: Uses the same kuzu_py wrapper across projects
2. **Package Reuse**: Leverages kuzu-py's custom KuzuDB build and extensions
3. **Consistent Python Environment**: Ensures all projects use the same Python 3.12 base
4. **Modular Design**: Additional packages (websockets, httpx) are added on top of kuzu-py

## Usage

The Python environment is available in:
- Development shell: `nix develop`
- Test runner: `nix run .#test`
- Direct Python access: `${pythonEnv}/bin/python`

## Alternative Approaches

If you need the complete kuzu-py environment including all its dependencies:

```nix
# Option 1: Use kuzu-py's pythonEnv directly
pythonEnv = kuzu-py.packages.${system}.pythonEnv;

# Option 2: Extend kuzu-py's environment
pythonEnv = pkgs.python312.withPackages (ps: 
  (kuzu-py.packages.${system}.pythonEnv.propagatedBuildInputs or []) ++ 
  [ ps.websockets ps.httpx ps.pytest-asyncio ]
);
```