{
  description = "HTTP-only OpenCode client - Core functionality only";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-darwin" "aarch64-linux" "x86_64-darwin" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f (import nixpkgs { inherit system; }));
    in {
      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          packages = with pkgs; [
            opencode
            curl
            jq
            netcat-gnu
          ];
          shellHook = ''
            echo "🚀 OpenCode HTTP Client (Core)"
            echo "Start server: nix run nixpkgs#opencode -- serve --port 4096"
            echo "Use client: nix run .#client-hello -- 'your message'"
          '';
        };
      });

      packages = forAllSystems (pkgs: {
        client-hello = pkgs.writeShellApplication {
          name = "opencode-client-hello";
          runtimeInputs = with pkgs; [ curl jq ];
          text = ''
            set -euo pipefail

            OPENCODE_URL="''${OPENCODE_URL:-http://127.0.0.1:4096}"
            MSG="''${1:-just say hi}"
            PROVIDER="''${OPENCODE_PROVIDER:-}"
            MODEL="''${OPENCODE_MODEL:-}"

            echo "[client] target: $OPENCODE_URL"

            # Health check
            if ! curl -fsS "$OPENCODE_URL/doc" >/dev/null; then
              echo "[client] error: server not reachable at $OPENCODE_URL" >&2
              echo "[hint] start: nix run nixpkgs#opencode -- serve --port 4096" >&2
              exit 1
            fi

            # Create session
            SID=$(curl -fsS -X POST "$OPENCODE_URL/session" \
              -H 'Content-Type: application/json' \
              -d '{}' | jq -r '.id')
            if [ -z "''${SID:-}" ] || [ "$SID" = "null" ]; then
              echo "[client] error: failed to create session" >&2
              exit 1
            fi
            echo "[client] session: $SID"

            # Build message payload  
            PAYLOAD=$(jq -n --arg text "$MSG" --arg p "$PROVIDER" --arg m "$MODEL" '
              { parts: [{ type: "text", text: $text }] }
              + (if $p != "" and $m != "" then { model: { providerID: $p, modelID: $m }} else {} end)
            ')

            # Send message
            RESP=$(curl -fsS -X POST "$OPENCODE_URL/session/$SID/message" \
              -H 'Content-Type: application/json' \
              -d "$PAYLOAD")

            # Extract response
            if echo "$RESP" | jq -e '.parts? // [] | length > 0' >/dev/null 2>&1; then
              echo "[client] reply:" && echo "$RESP" | jq -r '(.parts[]? | select(.type=="text") | .text) // empty'
            else
              echo "$RESP" | jq
            fi
          '';
          meta = {
            description = "Simple HTTP client for OpenCode (no session persistence)";
          };
        };
      });

      apps = forAllSystems (pkgs: {
        client-hello = {
          type = "app";
          program = "${self.packages.${pkgs.stdenv.system}.client-hello}/bin/opencode-client-hello";
        };
      });

      templates = {
        opencode-client = {
          path = ./templates/opencode-client;
          description = "Dynamic HTTP client template for OpenCode";
        };
        
        multi-agent = {
          path = ./templates/multi-agent;
          description = "Multi-agent system template with session management";
        };
      };
    };
}