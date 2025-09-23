{
  description = "MCP Unified Management Tool v2.0 - Production Perfect";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # Core dependencies for mcp-sync
        runtimeDeps = with pkgs; [
          bash
          jq
          findutils
          diffutils
          coreutils
          gawk
          gnugrep
        ];

        # Test script that runs the comprehensive test suite
        testScript = pkgs.writeShellScriptBin "mcp-test" ''
          set -euo pipefail

          echo ">ê MCP Management Tool - Comprehensive Test Suite"
          echo "==============================================="
          echo ""

          # Ensure we're in the right directory
          cd ${./.}

          # Run test harness with proper environment
          export PATH="${pkgs.lib.makeBinPath runtimeDeps}:$PATH"

          echo "Running comprehensive behavioral protection tests..."
          ./test-harness.sh

          echo ""
          echo "Running minimal integration tests..."
          ./test-minimal.sh

          echo ""
          echo " All tests completed successfully"
        '';

        # Development shell
        devShell = pkgs.mkShell {
          buildInputs = runtimeDeps ++ [
            pkgs.nix
          ];

          shellHook = ''
            echo "=' MCP Management Tool Development Environment"
            echo "============================================="
            echo ""
            echo "Available commands:"
            echo "  ./mcp-sync        - MCP synchronization tool"
            echo "  ./test-harness.sh - Comprehensive test suite"
            echo "  ./test-minimal.sh - Minimal integration tests"
            echo ""
            echo "Test execution:"
            echo "  nix run .#test    - Run full test suite"
            echo ""
          '';
        };

      in {
        # Test package
        packages.test = testScript;
        packages.default = testScript;

        # Development shell
        devShells.default = devShell;

        # Apps for nix run
        apps = {
          test = {
            type = "app";
            program = "${testScript}/bin/mcp-test";
          };
          default = {
            type = "app";
            program = "${testScript}/bin/mcp-test";
          };
        };
      });
}