# WASM Database Engine Assets

This directory contains Nix flakes for packaging WASM (WebAssembly) database engine assets as Nix derivations.

## Purpose

Each subdirectory contains a flake.nix that downloads and packages WASM assets from popular database engines that run in browsers and serverless environments. This allows for reproducible builds and easy integration into Nix-based projects.

## Supported Database Engines

### DuckDB (`duckdb/`)
- **Package**: `@duckdb/duckdb-wasm`
- **Version**: 1.28.1-dev106.0
- **Description**: Analytical SQL database engine for WASM

### SQLite (`sqlite/`)
- **Package**: `@sqlite.org/sqlite-wasm`
- **Version**: 3.50.4-build1
- **Description**: Official SQLite WASM with OPFS support
- **Features**: Persistent storage, worker API, Node.js support

### Kuzu (`kuzu/`)
- **Package**: `@kuzu/kuzu-wasm`
- **Version**: 1.0.4
- **Description**: Graph database engine for WASM

### PGlite (`pglite/`)
- **Package**: `@electric-sql/pglite`
- **Version**: 0.2.12
- **Description**: PostgreSQL in WASM for browser and serverless

## Usage

Each directory can be built independently:

```bash
cd duckdb/
nix build
```

Or reference as a flake input in your projects:

```nix
{
  inputs = {
    duckdb-wasm.url = "path:./poc/wasm/duckdb";
  };
  
  outputs = { self, duckdb-wasm, ... }: {
    # Use duckdb-wasm.packages.${system}.assets
  };
}
```

## TODO

- Fill in SHA256 hashes for package sources
- Complete WASM file extraction logic
- Add proper file existence checks in tests
- Document specific WASM asset locations within each package