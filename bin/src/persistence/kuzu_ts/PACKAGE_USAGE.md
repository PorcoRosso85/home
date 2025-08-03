# KuzuDB TypeScript Package Usage Guide

This guide provides detailed examples and best practices for using kuzu_ts as a packaged Nix flake in your projects.

## Table of Contents

1. [Basic Integration](#basic-integration)
2. [Advanced Usage](#advanced-usage)
3. [Development Workflow](#development-workflow)
4. [Troubleshooting](#troubleshooting)

## Basic Integration

### Minimal Flake Configuration

```nix
{
  description = "My sync project using kuzu_ts";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    kuzu-ts.url = "path:../../persistence/kuzu_ts";
  };

  outputs = { self, nixpkgs, flake-utils, kuzu-ts }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        kuzu = kuzu-ts.packages.${system}.default;
      in {
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "my-sync-app";
          version = "1.0.0";
          src = ./.;
          
          buildPhase = ''
            # Link kuzu_ts modules
            ln -s ${kuzu}/mod.ts deps/kuzu_ts.ts
            ln -s ${kuzu}/node_modules node_modules
          '';
          
          installPhase = ''
            mkdir -p $out
            cp -r * $out/
          '';
        };
      });
}
```

### Using in TypeScript/Deno

```typescript
// Import directly from the packaged module
import { createDatabase, createConnection } from "./deps/kuzu_ts.ts";

// Or with import map
// import_map.json:
{
  "imports": {
    "kuzu_ts": "./deps/kuzu_ts.ts"
  }
}

// Then in your code:
import { createDatabase, createConnection } from "kuzu_ts";
```

## Advanced Usage

### Complete Sync Application Example

```nix
{
  description = "WebSocket sync service with KuzuDB";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    kuzu-ts.url = "path:../../persistence/kuzu_ts";
    log-ts.url = "path:../../telemetry/log_ts";
  };

  outputs = { self, nixpkgs, flake-utils, kuzu-ts, log-ts }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        kuzu = kuzu-ts.packages.${system}.default;
      in {
        apps.server = {
          type = "app";
          program = "${pkgs.writeShellScript "sync-server" ''
            # Set up environment
            export KUZU_TS_PATH="${kuzu}"
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            
            # Create import map dynamically
            cat > /tmp/import_map.json <<EOF
            {
              "imports": {
                "kuzu_ts": "${kuzu}/mod.ts",
                "kuzu_ts/worker": "${kuzu}/worker/mod.ts",
                "log_ts": "${log-ts.lib.importPath}/mod.ts"
              }
            }
            EOF
            
            # Run server with all required permissions
            exec ${pkgs.deno}/bin/deno run \
              --allow-net \
              --allow-read \
              --allow-write \
              --allow-env \
              --allow-ffi \
              --unstable-ffi \
              --import-map=/tmp/import_map.json \
              ./server.ts
          ''}";
        };
        
        apps.test = {
          type = "app";
          program = "${pkgs.writeShellScript "run-tests" ''
            # The kuzu package includes everything needed
            export KUZU_TS_PATH="${kuzu}"
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            
            # Run tests
            ${pkgs.deno}/bin/deno test \
              --allow-all \
              --unstable-ffi \
              ./tests/*.test.ts
          ''}";
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            deno
            # No need to include kuzu deps - they're in the package!
          ];
          
          shellHook = ''
            echo "🔄 Sync Development Environment"
            echo "kuzu_ts is available at: ${kuzu}"
            
            # Set up development links
            mkdir -p deps
            ln -sf ${kuzu} deps/kuzu_ts
            
            # Environment for runtime
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
          '';
        };
      });
}
```

### TypeScript Usage Example

```typescript
// server.ts
import { createDatabase, createConnection } from "kuzu_ts";
import { Logger } from "log_ts";

const logger = new Logger("sync-server");

export class SyncServer {
  private db: any;
  private conn: any;
  
  async initialize() {
    // Create database - the package handles all native module loading
    this.db = await createDatabase("./sync.db");
    this.conn = await createConnection(this.db);
    
    // Initialize schema
    await this.conn.execute(`
      CREATE NODE TABLE IF NOT EXISTS SyncState(
        id STRING,
        version INT64,
        data STRING,
        timestamp INT64,
        PRIMARY KEY (id)
      )
    `);
    
    logger.info("Database initialized");
  }
  
  async syncData(id: string, data: any) {
    const timestamp = Date.now();
    const version = await this.getNextVersion(id);
    
    await this.conn.execute(`
      MERGE (s:SyncState {id: $id})
      ON CREATE SET s.version = $version, s.data = $data, s.timestamp = $timestamp
      ON MATCH SET s.version = $version, s.data = $data, s.timestamp = $timestamp
    `, { id, version, data: JSON.stringify(data), timestamp });
    
    return { id, version, timestamp };
  }
  
  private async getNextVersion(id: string): Promise<number> {
    const result = await this.conn.execute(
      "MATCH (s:SyncState {id: $id}) RETURN s.version as version",
      { id }
    );
    const rows = await result.getAll();
    return rows.length > 0 ? rows[0].version + 1 : 1;
  }
}
```

## Development Workflow

### 1. Local Development Setup

```bash
# Clone your project
git clone myproject
cd myproject

# Enter development shell
nix develop

# The shell automatically:
# - Links kuzu_ts to deps/
# - Sets up LD_LIBRARY_PATH
# - Provides deno command
```

### 2. Testing with Packaged KuzuDB

```typescript
// tests/integration.test.ts
import { assertEquals } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { createDatabase, createConnection } from "../deps/kuzu_ts/mod.ts";

Deno.test("KuzuDB integration", async () => {
  // The package provides everything needed
  const db = await createDatabase(":memory:");
  const conn = await createConnection(db);
  
  // Test your sync logic
  await conn.execute("CREATE NODE TABLE Test(id INT64, PRIMARY KEY(id))");
  await conn.execute("CREATE (:Test {id: 1})");
  
  const result = await conn.execute("MATCH (t:Test) RETURN count(t) as count");
  const rows = await result.getAll();
  
  assertEquals(rows[0].count, 1);
});
```

### 3. Building for Production

```nix
packages.sync-app = pkgs.stdenv.mkDerivation {
  pname = "sync-app";
  version = "1.0.0";
  
  src = ./.;
  
  buildPhase = ''
    # Copy kuzu_ts with all dependencies
    cp -r ${kuzu} $out/deps/kuzu_ts
    
    # Your build steps here
  '';
  
  installPhase = ''
    # Create self-contained package
    mkdir -p $out/bin
    
    # Wrapper script with all paths configured
    cat > $out/bin/sync-app <<'EOF'
    #!/bin/sh
    export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
    export KUZU_TS_PATH="$out/deps/kuzu_ts"
    exec ${pkgs.deno}/bin/deno run \
      --allow-all \
      --unstable-ffi \
      $out/server.ts "$@"
    EOF
    chmod +x $out/bin/sync-app
  '';
};
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Native Module Loading Errors

**Problem**: `Error: Cannot load native module`

**Solution**: Ensure LD_LIBRARY_PATH is set:
```bash
export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
```

#### 2. Import Resolution Issues

**Problem**: `Module not found: kuzu_ts`

**Solution**: Use proper import paths or import maps:
```typescript
// Direct import
import { createDatabase } from "./deps/kuzu_ts/mod.ts";

// Or with import map
// import_map.json
{
  "imports": {
    "kuzu_ts": "./deps/kuzu_ts/mod.ts"
  }
}
```

#### 3. Permission Errors

**Problem**: `PermissionDenied: Requires ffi access`

**Solution**: Add required Deno permissions:
```bash
deno run --allow-ffi --unstable-ffi your-app.ts
```

### Debug Mode

Enable detailed logging:

```typescript
// Enable debug logging
Deno.env.set("KUZU_DEBUG", "1");

// Your application code
const db = await createDatabase("./debug.db");
```

### Performance Tips

1. **Connection Pooling**: Reuse connections instead of creating new ones
2. **Batch Operations**: Use batch inserts for large data sets
3. **Indexing**: Create appropriate indexes for frequently queried fields

## Example Projects

### Minimal Sync Client

```typescript
// client.ts
import { createDatabase, createConnection } from "kuzu_ts";

const db = await createDatabase(":memory:");
const conn = await createConnection(db);

// Subscribe to remote changes
const ws = new WebSocket("ws://localhost:8080/sync");

ws.onmessage = async (event) => {
  const change = JSON.parse(event.data);
  
  // Apply change to local database
  await conn.execute(
    "MERGE (n:Node {id: $id}) SET n.data = $data",
    { id: change.id, data: change.data }
  );
};

// Send local changes
export async function syncLocal(id: string, data: any) {
  // Update local
  await conn.execute(
    "MERGE (n:Node {id: $id}) SET n.data = $data",
    { id, data: JSON.stringify(data) }
  );
  
  // Send to server
  ws.send(JSON.stringify({ id, data }));
}
```

## Best Practices

1. **Always use the packaged version** - Don't install kuzu separately
2. **Set environment variables** in your shell scripts
3. **Use import maps** for cleaner imports
4. **Test with `:memory:` databases** for unit tests
5. **Handle connection lifecycle** properly in production

## Migration Guide

If you're migrating from a manual kuzu installation:

1. Remove any npm/deno install commands for kuzu
2. Update your flake.nix to use kuzu-ts as input
3. Update imports to use the packaged module
4. Remove any patchelf or LD_LIBRARY_PATH workarounds
5. Test thoroughly with the packaged version

## Support

For issues specific to the kuzu_ts package:
- Check the package tests: `nix run .#test`
- Review the flake.nix for configuration details
- Ensure all environment variables are set correctly

For KuzuDB-specific questions:
- Refer to the [KuzuDB documentation](https://kuzudb.com/docs/)
- Check the mock implementation in `core/database.ts` for API reference