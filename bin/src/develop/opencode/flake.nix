{
  description = "HTTP-only two-server opencode dev env. Includes dynamic client, templates: opencode-client and multi-agent (session/message/orchestrator). Pre-auth assumed.";

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
            netcat-gnu  # Provides 'nc' with GNU-specific options like -c for test compatibility
          ];
          shellHook = ''
            echo "Start server: nix run nixpkgs#opencode -- serve --port 4096"
            echo "See README.md for usage details and templates"
          '';
        };
      });

      # HTTP client: nix run .#opencode-client -- 'just say hi' (or .#client-hello for backward compatibility)
      packages = forAllSystems (pkgs: {
        opencode-client = pkgs.writeShellApplication {
          name = "opencode-client";
          runtimeInputs = with pkgs; [ curl jq ];
          text = ''
            set -euo pipefail

            OPENCODE_URL="''${OPENCODE_URL:-http://127.0.0.1:4096}"
            MSG="''${1:-just say hi}"
            PROVIDER="''${OPENCODE_PROVIDER:-}"
            MODEL="''${OPENCODE_MODEL:-}"
            PROJECT_DIR="''${OPENCODE_PROJECT_DIR:-$(pwd)}"

            echo "[client] target: $OPENCODE_URL" >&2
            echo "[client] project: $PROJECT_DIR" >&2

            # Early directory validation
            if [ ! -d "$PROJECT_DIR" ]; then
              echo "[client] error: directory not found: $PROJECT_DIR" >&2
              exit 1
            fi

            # Source session management functions (DRY compliance)
            ${builtins.readFile ./lib/session-helper.sh}
            # 1) Health check (OpenAPI doc)
            if ! oc_session_http_get "$OPENCODE_URL/doc" >/dev/null; then
              echo "[client] error: server not reachable at $OPENCODE_URL" >&2
              echo "[hint] start: nix run nixpkgs#opencode -- serve --port 4096" >&2
              exit 1
            fi

            # 2) Get or create session with directory-based continuity
            SID=$(oc_session_get_or_create "$OPENCODE_URL" "$PROJECT_DIR")
            if [ -z "''${SID:-}" ]; then
              exit 1
            fi

            # 3) Build message payload dynamically
            #    If PROVIDER/MODEL are given, include them; otherwise rely on server defaults.
            PAYLOAD=$(jq -n --arg text "$MSG" --arg p "$PROVIDER" --arg m "$MODEL" '
              { parts: [{ type: "text", text: $text }] }
              + (if $p != "" and $m != "" then { model: { providerID: $p, modelID: $m }} else {} end)
            ')

            # 4) Send message
            RESP=$(oc_session_http_post "$OPENCODE_URL/session/$SID/message" "$PAYLOAD")

            # 5) Extract a concise text response when available
            #    Fallback to printing the whole JSON if structure differs.
            if echo "$RESP" | jq -e '.parts? // [] | length > 0' >/dev/null 2>&1; then
              echo "[client] reply:" >&2 && echo "$RESP" | jq -r '(.parts[]? | select(.type=="text") | .text) // empty'
            else
              echo "$RESP" | jq
            fi
          '';
          meta = {
            description = "HTTP client (dir-based session continuity; pre-auth; POST /session/:id/message)";
          };
        };
      });

      apps = forAllSystems (pkgs: {
        opencode-client = {
          type = "app";
          program = "${self.packages.${pkgs.stdenv.system}.opencode-client}/bin/opencode-client";
        };
        # Backward compatibility alias
        client-hello = {
          type = "app";
          program = "${self.packages.${pkgs.stdenv.system}.opencode-client}/bin/opencode-client";
        };
      });

      # Templates to scaffold clients into project directories
      templates = {
        # Usage: nix flake init -t .#opencode-client
        opencode-client = {
          path = ./templates/opencode-client;
          description = "Dynamic HTTP client template for opencode (pre-auth assumed)";
        };
        
        # Usage: nix flake init -t .#multi-agent
        multi-agent = {
          path = ./templates/multi-agent;
          description = "HTTP multi-agent template (session/message/orchestrator)";
        };
      };
    };
}
