{
  description = "TypeScript implementation of universal log API";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    let
      # Overlay that provides the log_ts module
      overlay = final: prev: {
        log_ts = {
          # Path to import the module from
          importPath = ./.;
          # Module URL for Deno imports
          moduleUrl = "file://${./.}/mod.ts";
          # Package metadata
          meta = {
            description = "TypeScript logging implementation for telemetry";
            version = "1.0.0";
          };
        };
      };
    in
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ overlay ];
        };
        
        # Deno environment with proper permissions
        denoEnv = pkgs.writeShellScriptBin "deno-env" ''
          export DENO_DIR="$PWD/.deno"
          ${pkgs.deno}/bin/deno "$@"
        '';
      in
      {
        # Export the overlay for other flakes to use
        overlays.default = overlay;
        
        # Package outputs
        packages = {
          # The module itself (reference to source)
          default = pkgs.stdenv.mkDerivation {
            pname = "log_ts";
            version = "1.0.0";
            src = ./.;
            
            installPhase = ''
              mkdir -p $out/lib
              cp -r * $out/lib/
            '';
            
            meta = {
              description = "TypeScript logging implementation for telemetry";
              platforms = pkgs.lib.platforms.all;
            };
          };
          
          # Test runner package
          test = pkgs.writeShellScriptBin "test-log-ts" ''
            set -e
            echo "=== Running log_ts tests ==="
            cd ${self}
            ${denoEnv}/bin/deno-env test --allow-read --allow-env
          '';
          
          # Type checking package
          check = pkgs.writeShellScriptBin "check-log-ts" ''
            set -e
            echo "=== Type checking log_ts ==="
            cd ${self}
            ${denoEnv}/bin/deno-env check mod.ts
          '';
        };
        
        # Development shell
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            deno
            nodejs_20  # For Node.js compatibility
            nodePackages.typescript
          ];
          
          shellHook = ''
            echo "log_ts development environment"
            echo "Deno version: $(deno --version | head -n1)"
            echo ""
            echo "Available commands:"
            echo "  deno test    - Run tests"
            echo "  deno check   - Type check"
            echo "  nix run .#test   - Run tests via Nix"
            echo "  nix run .#check  - Type check via Nix"
          '';
        };
        
        # Apps
        apps = {
          # Run tests
          test = {
            type = "app";
            program = "${self.packages.${system}.test}/bin/test-log-ts";
          };
          
          # Type check
          check = {
            type = "app";
            program = "${self.packages.${system}.check}/bin/check-log-ts";
          };
          
          # Deno REPL with module available
          repl = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "log-ts-repl" ''
              echo "Starting Deno REPL with log_ts module..."
              echo "You can import the module with:"
              echo "  const { log } = await import('${./.}/mod.ts');"
              cd ${self}
              ${denoEnv}/bin/deno-env repl --allow-read --allow-env
            ''}/bin/log-ts-repl";
          };
          
          default = self.apps.${system}.test;
        };
      })
    # Export overlay and lib at the flake level for easier consumption
    // {
      overlays.default = overlay;
      
      # Direct access to module metadata for other flakes
      lib = {
        importPath = ./.;
        moduleUrl = "file://${./.}/mod.ts";
        # Helper function to create import map entry
        importMapEntry = name: {
          "${name}" = "file://${./.}/mod.ts";
        };
      };
    };
}