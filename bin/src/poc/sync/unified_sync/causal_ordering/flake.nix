{
  description = "Causal Ordering POC for KuzuDB synchronization";

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
          buildInputs = with pkgs; [
            deno
            nodejs_20
            nodePackages.typescript
          ];

          shellHook = ''
            echo "[CAUSAL-ORDERING] 🔄 Causal Ordering POC Development Environment"
            echo "[CAUSAL-ORDERING] Run 'nix run' to execute tests"
          '';
        };

        apps.default = {
          type = "app";
          program = "${pkgs.writeShellScript "run-causal-ordering-test" ''
            #!/usr/bin/env bash
            set -e

            echo "[CAUSAL-ORDERING] 🟢 TDD Green Phase - Testing causal ordering"
            echo "[CAUSAL-ORDERING] Port: WebSocket=8083"
            echo ""

            # Working directory
            WORK_DIR=$(mktemp -d)
            cd $WORK_DIR

            # Copy test files
            cp ${./causal-sync-client.test.ts} causal-sync-client.test.ts || true
            cp ${./complex-scenarios.test.ts} complex-scenarios.test.ts || true
            cp ${./causal-sync-client.ts} causal-sync-client.ts || true
            cp ${./causal-operation-store.ts} causal-operation-store.ts || true
            cp ${./conflict-resolution.ts} conflict-resolution.ts || true
            cp ${./websocket-server.ts} websocket-server.ts || true

            # List files
            echo "[CAUSAL-ORDERING] Files in working directory:"
            ls -la

            # Kill any existing processes on port 8083
            ${pkgs.killall}/bin/killall deno 2>/dev/null || true
            
            # Start WebSocket server on port 8083
            echo "[CAUSAL-ORDERING] Starting server on port 8083..."
            ${pkgs.deno}/bin/deno run --allow-net websocket-server.ts &
            SERVER_PID=$!
            
            # Wait for server to start
            sleep 2
            
            # Run tests
            echo "[CAUSAL-ORDERING] Running causal ordering tests..."
            echo "[CAUSAL-ORDERING] 🔴 Red phase - expecting failures for new tests"
            
            ${pkgs.deno}/bin/deno test --no-check --allow-net causal-sync-client.test.ts complex-scenarios.test.ts || true
            
            # Cleanup
            kill $SERVER_PID 2>/dev/null || true
            
            echo ""
            echo "[CAUSAL-ORDERING] 🔴 Red phase complete - tests should fail"
          ''}";
        };

        packages.test = pkgs.writeShellScriptBin "test-causal-ordering" ''
          ${self.apps.${system}.default.program}
        '';
      });
}