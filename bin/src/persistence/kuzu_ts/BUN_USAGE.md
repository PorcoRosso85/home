# Bun Support for KuzuDB TypeScript

## Overview

The kuzu_ts package now includes official Bun runtime support, allowing you to use KuzuDB in Bun applications with a simplified API and Nix packaging.

## Installation

### Using Nix Flakes

Add kuzu_ts as an input to your `flake.nix`:

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    kuzu-ts.url = "path:../../persistence/kuzu_ts";
    # or from git: "github:yourrepo/kuzu_ts"
  };

  outputs = { self, nixpkgs, flake-utils, kuzu-ts }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        # Get the Bun-specific package
        kuzuBun = kuzu-ts.packages.${system}.bun;
      in
      {
        # Use in your packages
        packages.myapp = pkgs.stdenv.mkDerivation {
          name = "my-kuzu-app";
          buildInputs = [ pkgs.bun kuzuBun ];
          # ... rest of your derivation
        };

        # Or in dev shells
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            bun
            kuzuBun
          ];
          
          shellHook = ''
            echo "KuzuDB Bun environment ready!"
            export KUZU_TS_PATH="${kuzuBun}/lib/kuzu_ts_bun"
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
          '';
        };
      });
}
```

### Development Shell

For quick development, use the provided Bun dev shell:

```bash
# Enter the Bun development environment
nix develop .#bun

# Your environment now has:
# - Bun runtime
# - Pre-installed kuzu npm package
# - Properly patched native bindings
# - Configured library paths
```

## Usage

### Simple Wrapper API

The Bun package provides a simplified wrapper API that avoids Deno-specific imports:

```typescript
import { 
  createDatabase, 
  createConnection, 
  executeQuery, 
  getAllRows 
} from "@kuzu-ts/bun/simple_wrapper";

// Create a database
const db = await createDatabase("./mydb");

// Create a connection
const conn = await createConnection(db);

// Execute queries
await executeQuery(conn, "CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY (name))");
await executeQuery(conn, "CREATE (:Person {name: 'Alice', age: 30})");

// Query and get results
const result = await executeQuery(conn, "MATCH (p:Person) RETURN p.name, p.age");
const rows = getAllRows(result);
console.log(rows);
```

### Direct npm:kuzu Usage

If you need full control, you can also use the kuzu package directly:

```typescript
import { kuzu } from "@kuzu-ts/bun/simple_wrapper";
// or
import kuzu from "kuzu";

const db = new kuzu.Database("./mydb");
const conn = new kuzu.Connection(db);
// ... use the native kuzu API
```

## Current Limitations

1. **TypeScript Layer Compatibility**: The main TypeScript implementation (`mod.ts`) contains Deno-specific imports that are not compatible with Bun. Use the simple wrapper API or direct npm:kuzu access instead.

2. **Worker Implementation**: The worker-based implementation is not available for Bun. Use the synchronous API provided by the simple wrapper.

3. **Import Maps**: Bun doesn't support Deno's import maps, so dependency resolution works differently. The package handles this transparently when using the provided APIs.

## Example Application

Here's a complete example Bun application using kuzu_ts:

```typescript
// app.ts
import { 
  createDatabase, 
  createConnection, 
  executeQuery, 
  getAllRows 
} from "@kuzu-ts/bun/simple_wrapper";

async function main() {
  console.log("🚀 Starting KuzuDB Bun example");
  
  // Create in-memory database
  const db = await createDatabase(":memory:");
  const conn = await createConnection(db);
  
  // Create schema
  await executeQuery(conn, `
    CREATE NODE TABLE User(
      id INT64, 
      name STRING, 
      email STRING,
      PRIMARY KEY (id)
    )
  `);
  
  await executeQuery(conn, `
    CREATE REL TABLE Follows(
      FROM User TO User,
      since DATE
    )
  `);
  
  // Insert data
  await executeQuery(conn, "CREATE (:User {id: 1, name: 'Alice', email: 'alice@example.com'})");
  await executeQuery(conn, "CREATE (:User {id: 2, name: 'Bob', email: 'bob@example.com'})");
  await executeQuery(conn, "MATCH (a:User), (b:User) WHERE a.id = 1 AND b.id = 2 CREATE (a)-[:Follows {since: date('2024-01-01')}]->(b)");
  
  // Query data
  const result = await executeQuery(conn, `
    MATCH (u1:User)-[f:Follows]->(u2:User) 
    RETURN u1.name as follower, u2.name as following, f.since as since
  `);
  
  const rows = getAllRows(result);
  console.log("Query results:", rows);
}

main().catch(console.error);
```

Run it with:

```bash
bun run app.ts
```

## Performance Considerations

Bun's runtime offers several performance advantages:

- **Fast startup**: Bun's quick initialization reduces cold start times
- **Native TypeScript**: No transpilation overhead
- **Optimized runtime**: Bun's JavaScriptCore engine provides excellent performance
- **Efficient FFI**: Native module calls are optimized in Bun

## Troubleshooting

### Library Loading Issues

If you encounter errors about missing libraries:

```bash
# Ensure LD_LIBRARY_PATH is set correctly
export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
```

### Module Resolution

If Bun can't find the kuzu module:

```bash
# Ensure node_modules are accessible
bun install  # In development
# or use the Nix-packaged version which includes pre-installed modules
```

## Future Improvements

1. **Full TypeScript API**: Port the complete TypeScript interface to be Bun-compatible
2. **Worker Support**: Implement Bun worker threads for parallel processing
3. **Performance Benchmarks**: Comprehensive comparison with Deno and Node.js implementations
4. **Streaming API**: Add streaming query result support optimized for Bun

## See Also

- [Main README](./README.md) - General kuzu_ts documentation
- [Bun Implementation](./bun/README.md) - Technical details of the Bun implementation
- [Package Usage](./PACKAGE_USAGE.md) - General packaging information