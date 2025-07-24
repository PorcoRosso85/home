# Using log_ts as a Flake Input

## Example 1: Using in another TypeScript/Deno project

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    log-ts.url = "path:../telemetry/log_ts";  # or use github URL
  };

  outputs = { self, nixpkgs, log-ts }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [ deno ];
        
        shellHook = ''
          # Use the module path from the flake
          export LOG_TS_PATH="${log-ts.lib.importPath}"
          echo "log_ts module available at: $LOG_TS_PATH"
        '';
      };
      
      # Example app using the log module
      apps.${system}.default = {
        type = "app";
        program = "${pkgs.writeShellScriptBin "run" ''
          # Create a temporary import map
          cat > import_map.json <<EOF
          {
            "imports": {
              "@telemetry/log": "${log-ts.lib.moduleUrl}"
            }
          }
          EOF
          
          # Run with import map
          ${pkgs.deno}/bin/deno run --import-map=import_map.json --allow-read --allow-env main.ts
        ''}/bin/run";
      };
    };
}
```

## Example 2: Using the overlay

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    log-ts.url = "path:../telemetry/log_ts";
  };

  outputs = { self, nixpkgs, log-ts }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
        overlays = [ log-ts.overlays.default ];
      };
    in
    {
      # Now pkgs.log_ts is available
      packages.${system}.default = pkgs.stdenv.mkDerivation {
        name = "my-app";
        buildInputs = [ pkgs.deno ];
        
        buildPhase = ''
          echo "Using log_ts from: ${pkgs.log_ts.importPath}"
          echo "Module URL: ${pkgs.log_ts.moduleUrl}"
        '';
      };
    };
}
```

## Example 3: Direct import in TypeScript

```typescript
// Import using the module URL provided by the flake
import { log } from "@telemetry/log";  // When using import map
// Or direct import:
// import { log } from "file:///path/to/log_ts/mod.ts";

// Use the log function
await log({
  level: "INFO",
  message: "Application started",
  timestamp: new Date().toISOString()
});
```

## Available Flake Outputs

- **overlays.default**: Provides `log_ts` package to nixpkgs
- **lib.importPath**: Direct path to the module source
- **lib.moduleUrl**: Deno-compatible file:// URL for imports
- **lib.importMapEntry**: Helper to create import map entries
- **packages.<system>.default**: The module as a Nix package
- **packages.<system>.test**: Test runner script
- **packages.<system>.check**: Type checking script
- **devShells.<system>.default**: Development environment with Deno
- **apps.<system>.test**: Run tests
- **apps.<system>.check**: Run type checking
- **apps.<system>.repl**: Deno REPL with module available