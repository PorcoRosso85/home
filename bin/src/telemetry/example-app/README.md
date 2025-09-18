# Example App - Telemetry Log Module Usage

This example demonstrates how to use the telemetry log modules as flake inputs.

## Usage

### TypeScript Module

```nix
# In your flake.nix
inputs.log-ts.url = "path:../telemetry/log_ts";

# Access the module
"${log-ts.lib.importPath}/mod.ts"
```

### Running the Example

```bash
# Enter development shell
nix develop

# Run TypeScript example
nix run .#test-ts
```

## Module Paths

- TypeScript: `telemetry/log_ts/`
- Python: `telemetry/log_py/` (currently has build issues)

## Features Demonstrated

1. Importing log modules as flake inputs
2. Using the module in TypeScript/Deno
3. Outputting JSONL format logs to stdout