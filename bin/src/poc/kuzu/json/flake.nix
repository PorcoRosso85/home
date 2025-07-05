{
  description = "KuzuDB JSON POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Test script wrapper
        testScript = pkgs.writeShellScriptBin "test-kuzu-json" ''
          #!${pkgs.bash}/bin/bash
          set -e
          
          export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib"
          echo "🧪 Running KuzuDB JSON tests..."
          
          # Create temp directory for test execution
          WORK_DIR=$(mktemp -d)
          trap "rm -rf $WORK_DIR" EXIT
          
          # Copy source files more reliably
          cp -r ${self}/. $WORK_DIR/
          # Fix permissions for the copied files
          chmod -R u+w $WORK_DIR
          cd $WORK_DIR
          
          # Install dependencies
          ${pkgs.uv}/bin/uv sync
          
          # Run tests
          ${pkgs.uv}/bin/uv run pytest -v "$@"
        '';
        
        # Demo script wrapper
        demoScript = pkgs.writeShellScriptBin "demo-kuzu-json" ''
          #!${pkgs.bash}/bin/bash
          set -e
          
          export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib"
          echo "📋 Running KuzuDB JSON demo..."
          
          # Create temp directory for execution
          WORK_DIR=$(mktemp -d)
          trap "rm -rf $WORK_DIR" EXIT
          
          # Copy source files more reliably
          cp -r ${self}/. $WORK_DIR/
          # Fix permissions for the copied files
          chmod -R u+w $WORK_DIR
          cd $WORK_DIR
          
          # Install dependencies
          ${pkgs.uv}/bin/uv sync
          
          # Run demo
          ${pkgs.uv}/bin/uv run python -m kuzu_json_poc "$@"
        '';
        
        # README display script (規約必須)
        readmeScript = pkgs.writeShellScriptBin "show-readme" ''
          #!${pkgs.bash}/bin/bash
          if [ -f "${self}/README.md" ]; then
            cat "${self}/README.md"
          else
            echo "README.md not found"
            exit 1
          fi
        '';
      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            python311
            ruff
            uv
            # C++ runtime libraries for kuzu
            stdenv.cc.cc.lib
          ];
          
          # Automatically set library paths for KuzuDB
          LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";
          
          shellHook = ''
            echo "KuzuDB JSON POC environment"
            echo "Python: $(python --version)"
            echo ""
            echo "Commands:"
            echo "  uv sync                    - Install dependencies"
            echo "  uv run pytest -v           - Run all tests"
            echo "  nix run .#test             - Run tests via nix"
          '';
        };
        
        # Applications
        apps = {
          # Default - show README (規約必須)
          default = {
            type = "app";
            program = "${readmeScript}/bin/show-readme";
          };
          
          # Test runner
          test = {
            type = "app";
            program = "${testScript}/bin/test-kuzu-json";
          };
          
          # Run demo
          demo = {
            type = "app";
            program = "${demoScript}/bin/demo-kuzu-json";
          };
        };
      });
}