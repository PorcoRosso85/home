{
  description = "A development environment for the kuzu_migration project";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          # The Nix packages available in the development environment
          packages = with pkgs; [
            python311
            ruff
            uv # For managing python dependencies
            # C++ runtime libraries for kuzu
            stdenv.cc.cc.lib
            deno # Add deno for causal_with_migration tests
            nodejs_20
            nodePackages.typescript
          ];
          
          # Automatically set library paths for KuzuDB
          LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";
          
          shellHook = ''
            echo "KuzuDB Migration Framework Development Environment"
            echo "Python: $(python --version)"
            echo "Deno: $(deno --version | head -1)"
            echo ""
            echo "Commands:"
            echo "  uv sync                    - Install dependencies"
            echo "  uv run pytest -v           - Run all tests"
            echo "  nix run .#test             - Run tests via nix"
            echo "  nix run .#test-causal      - Run causal_with_migration tests"
          '';
        };
        
        # Applications
        apps = {
          # Test runner
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib"
              echo "🧪 Running KuzuDB Migration tests..."
              exec ${pkgs.uv}/bin/uv run pytest -v "$@"
            ''}";
          };
          
          # Run example usage
          example = {
            type = "app";
            program = "${pkgs.writeShellScript "example" ''
              export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib"
              echo "📋 Running example usage..."
              exec ${pkgs.uv}/bin/uv run python example_usage.py "$@"
            ''}";
          };
          
          # Test causal_with_migration
          test-causal = {
            type = "app";
            program = "${pkgs.writeShellScript "test-causal" ''
              cd causal_with_migration
              
              # Kill any existing servers
              ${pkgs.killall}/bin/killall deno 2>/dev/null || true
              
              # Start WebSocket server
              ${pkgs.deno}/bin/deno run --allow-net websocket-server.ts &
              SERVER_PID=$!
              
              # Wait for server startup
              sleep 2
              
              # Run tests
              ${pkgs.deno}/bin/deno test \
                --no-check \
                --allow-net \
                --v8-flags=--max-old-space-size=512 \
                --unstable \
                --trace-leaks \
                causal-sync-client.test.ts causal-ddl-integration.test.ts "$@"
              TEST_RESULT=$?
              
              # Cleanup
              kill $SERVER_PID 2>/dev/null || true
              ${pkgs.killall}/bin/killall deno 2>/dev/null || true
              
              exit $TEST_RESULT
            ''}";
          };
        };
      });
}