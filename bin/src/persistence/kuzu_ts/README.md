# kuzu_ts - KuzuDB TypeScript/Deno Persistence Layer

## Overview

TypeScript/Deno implementation of the KuzuDB persistence layer, providing the same interface as kuzu_py but for TypeScript/Deno environments.

## Current Status

This implementation uses a mock KuzuDB adapter due to the challenges of using native Node.js modules in Deno. The interface is complete and tests are passing, but actual KuzuDB integration requires one of:

1. **Native Deno FFI binding** to KuzuDB C++ library
2. **WebAssembly build** of KuzuDB
3. **Node.js compatibility layer** improvements in Deno

## Usage

```typescript
import { createDatabase, createConnection } from "./mod.ts";

// Create in-memory database
const db = await createDatabase(":memory:");
const conn = await createConnection(db);

// Execute queries
await conn.execute("CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY (name))");
await conn.execute("CREATE (:Person {name: 'Alice', age: 30})");

const result = await conn.execute("MATCH (p:Person) RETURN p.name, p.age");
const rows = await result.getAll();
```

## Features

- ✅ Database factory with caching
- ✅ In-memory and persistent database support
- ✅ Test-specific unique instances
- ✅ TypeScript type definitions
- ✅ Deno-first design

## Testing

```bash
nix run .#test
# or
deno test --allow-read --allow-write --allow-net --allow-env
```

## Structure

```
kuzu_ts/
├── flake.nix      # Nix configuration
├── deno.json      # Deno configuration
├── mod.ts         # Main entry point
├── core/
│   └── database.ts # Database factory implementation
└── tests/
    └── database_test.ts # Unit tests
```

## Using as a Flake Input

This package is designed to be consumed as a Nix flake input by other projects. The package includes pre-installed and patched node_modules, making it easy to use in sync projects.

### Example flake.nix for sync projects

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    kuzu-ts.url = "path:../../persistence/kuzu_ts";
    # or from git: "github:yourrepo/kuzu_ts"
  };

  outputs = { self, nixpkgs, kuzu-ts }:
    let
      system = "x86_64-linux"; # or your system
      pkgs = nixpkgs.legacyPackages.${system};
    in {
      apps.${system}.myapp = {
        type = "app";
        program = "${pkgs.writeShellScript "myapp" ''
          # The package includes node_modules with patched native bindings
          export KUZU_TS_PATH="${kuzu-ts.packages.${system}.default}"
          exec ${pkgs.deno}/bin/deno run \
            --allow-read --allow-write --allow-net --allow-env --allow-ffi \
            --import-map="${kuzu-ts.packages.${system}.default}/import_map.json" \
            your-app.ts
        ''}";
      };
    };
}
```

### Node Modules Inclusion

The packaged kuzu_ts includes:
- Pre-installed `node_modules` with the KuzuDB npm package
- Native bindings patched for Nix compatibility using `patchelf`
- Proper runtime library paths configured via `LD_LIBRARY_PATH`
- Deno configuration with `nodeModulesDir: "auto"` for npm compatibility

This means sync projects don't need to:
- Install npm dependencies themselves
- Deal with native module compatibility issues
- Configure library paths for C++ dependencies

### Import Map Support

The package uses Deno's import map for dependency management:

```json
{
  "imports": {
    "kuzu": "npm:kuzu@0.10.0",
    "log_ts/": "./deps/log_ts/"
  }
}
```

When using kuzu_ts as a flake input, you can either:
1. Use the package's import paths directly
2. Create your own import map that references the packaged modules
3. Use the provided wrapper scripts that handle all configuration

For detailed examples and advanced usage patterns, see [PACKAGE_USAGE.md](./PACKAGE_USAGE.md).

## Future Work

1. Replace mock implementation with actual KuzuDB bindings
2. Add more comprehensive type definitions
3. Implement streaming query results
4. Add connection pooling support