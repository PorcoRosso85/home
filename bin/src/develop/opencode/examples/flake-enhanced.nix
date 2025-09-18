{
  description = "OpenCode Enhanced Client - Core + Directory Configuration";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-darwin" "aarch64-linux" "x86_64-darwin" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f (import nixpkgs { inherit system; }));
      
      # Configuration loader - reads .opencode-client.nix if exists
      loadDirConfig = pkgs: workDir: 
        let
          configPath = "${workDir}/.opencode-client.nix";
          defaultConfig = {
            sessionManagement.enabled = false;
            defaults = {};
            features = {};
          };
        in
          if builtins.pathExists configPath 
          then import configPath
          else defaultConfig;
          
    in {
      packages = forAllSystems (pkgs: {
        client-hello = pkgs.writeShellApplication {
          name = "opencode-client-enhanced";
          runtimeInputs = with pkgs; [ curl jq ];
          text = ''
            set -euo pipefail
            
            OPENCODE_URL="''${OPENCODE_URL:-http://127.0.0.1:4096}"
            MSG="''${1:-just say hi}"
            PROVIDER="''${OPENCODE_PROVIDER:-}"
            MODEL="''${OPENCODE_MODEL:-}"
            
            echo "[client] target: $OPENCODE_URL"
            
            # Check for directory configuration
            CONFIG_FILE="''${PWD}/.opencode-client.nix"
            SESSION_ENABLED=false
            
            if [[ -f "$CONFIG_FILE" ]]; then
              echo "[client] found directory config: $(basename "$CONFIG_FILE")"
              # Simple parsing for session management enabled
              if grep -q "sessionManagement.*enabled.*=.*true" "$CONFIG_FILE" 2>/dev/null; then
                SESSION_ENABLED=true
                echo "[client] session management: enabled"
              else
                echo "[client] session management: disabled"
              fi
            else
              echo "[client] no directory config, using core mode"
            fi
            
            # Health check
            if ! curl -fsS "$OPENCODE_URL/doc" >/dev/null; then
              echo "[client] error: server not reachable at $OPENCODE_URL" >&2
              echo "[hint] start: nix run nixpkgs#opencode -- serve --port 4096" >&2
              exit 1
            fi
            
            # Session handling based on configuration
            if [[ "$SESSION_ENABLED" == "true" ]]; then
              # Enhanced mode: Directory-based session continuity
              echo "[client] using enhanced session management"
              
              # Load session management functions
              session_get_base_dir() {
                  local state_base="''${XDG_STATE_HOME:-$HOME/.local/state}"
                  echo "$state_base/opencode/sessions"
              }
              
              session_get_file_path() {
                  local url="$1"
                  local current_dir="''${2:-$(pwd)}"
                  
                  url="''${url%/}"
                  local host_port="''${url#*://}"
                  host_port="''${host_port%%/*}"
                  
                  local abs_path
                  abs_path=$(cd "$current_dir" && pwd)
                  local project_name
                  project_name=$(echo "$abs_path" | sed 's/\\//_/g' | sed 's/^_//')
                  
                  local session_base
                  session_base=$(session_get_base_dir)
                  echo "$session_base/$host_port/$project_name.session"
              }
              
              session_get_or_create() {
                  local url="$1"
                  url="''${url%/}"
                  
                  local session_file
                  session_file=$(session_get_file_path "$url")
                  
                  local existing_session=""
                  if [[ -f "$session_file" ]]; then
                      existing_session=$(cat "$session_file" 2>/dev/null || echo "")
                  fi
                  
                  if [[ -n "$existing_session" ]]; then
                      if curl -fsS --max-time 10 "$url/session/$existing_session" >/dev/null 2>&1; then
                          echo "[client] session: $existing_session (resumed)" >&2
                          echo "$existing_session"
                          return 0
                      fi
                  fi
                  
                  local new_session
                  if new_session=$(curl -fsS -X POST "$url/session" \
                      -H 'Content-Type: application/json' \
                      -d '{}' | jq -r '.id' 2>/dev/null); then
                      
                      if [[ -n "$new_session" && "$new_session" != "null" ]]; then
                          mkdir -p "$(dirname "$session_file")"
                          echo "$new_session" > "$session_file"
                          echo "[client] session: $new_session (new)" >&2
                          echo "$new_session"
                          return 0
                      fi
                  fi
                  
                  echo "[client] error: failed to create session" >&2
                  return 1
              }
              
              # Get or create session
              SID=$(session_get_or_create "$OPENCODE_URL")
              if [ -z "''${SID:-}" ]; then
                exit 1
              fi
            else
              # Core mode: Simple session creation
              echo "[client] using core session management"
              SID=$(curl -fsS -X POST "$OPENCODE_URL/session" \
                -H 'Content-Type: application/json' \
                -d '{}' | jq -r '.id')
              if [ -z "''${SID:-}" ] || [ "$SID" = "null" ]; then
                echo "[client] error: failed to create session" >&2
                exit 1
              fi
              echo "[client] session: $SID (temporary)"
            fi
            
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
            description = "Enhanced OpenCode client with directory-based configuration support";
          };
        };
      });

      apps = forAllSystems (pkgs: {
        client-hello = {
          type = "app";
          program = "${self.packages.${pkgs.stdenv.system}.client-hello}/bin/opencode-client-enhanced";
        };
      });
      
      # Development shell with enhanced tools
      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          packages = with pkgs; [
            opencode
            curl
            jq
            netcat-gnu
          ];
          shellHook = ''
            echo "🚀 OpenCode Enhanced Development Environment"
            echo ""
            echo "📋 Available modes:"
            echo "  • Core mode: No .opencode-client.nix (simple HTTP client)"
            echo "  • Enhanced mode: With .opencode-client.nix (session continuity)"
            echo ""
            echo "⚡ Quick start:"
            echo "  nix run .#client-hello -- 'your message'"
            echo ""
            echo "🔧 Create directory config:"
            echo "  cp .opencode-client.nix /path/to/your/project/"
            echo ""
          '';
        };
      });
    };
}