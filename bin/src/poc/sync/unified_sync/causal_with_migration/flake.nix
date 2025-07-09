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
            echo "[CAUSAL-ORDERING] Run tests with: nix run .#test"
          '';
        };

        apps = {
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              cd ${./.}
              
              # Kill any existing servers
              ${pkgs.killall}/bin/killall deno 2>/dev/null || true
              
              # Start WebSocket server
              ${pkgs.deno}/bin/deno run --allow-net --allow-env websocket-server-enhanced.ts &
              SERVER_PID=$!
              
              # Wait for server startup
              sleep 2
              
              # Run tests
              ${pkgs.deno}/bin/deno test \
                --no-check \
                --allow-net \
                --allow-read \
                --allow-write \
                --allow-env \
                --v8-flags=--max-old-space-size=512 \
                causal-ddl-integration-improved.test.ts "$@"
              TEST_RESULT=$?
              
              # Cleanup
              kill $SERVER_PID 2>/dev/null || true
              ${pkgs.killall}/bin/killall deno 2>/dev/null || true
              
              exit $TEST_RESULT
            ''}";
          };
          
          test-all = {
            type = "app";
            program = "${pkgs.writeShellScript "test-all" ''
              cd ${./.}
              ${pkgs.deno}/bin/deno test \
                --no-check \
                --allow-net \
                --allow-run \
                --v8-flags=--max-old-space-size=512 \
                *.test.ts "$@"
            ''}";
          };
          
          test-clean = {
            type = "app";
            program = "${pkgs.writeShellScript "test-clean" ''
              cd ${./.}
              ${pkgs.deno}/bin/deno test \
                --no-check \
                --allow-net \
                --allow-read \
                --allow-write \
                --allow-env \
                --allow-run \
                causal-ddl-integration-clean.test.ts "$@"
            ''}";
          };
        };
      });
}