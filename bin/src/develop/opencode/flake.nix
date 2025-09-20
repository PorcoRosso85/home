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
          checkPhase = ''
            # Skip shellcheck for external file references
            ${pkgs.stdenv.shell} -n $target
          '';
          text = ''
            set -euo pipefail

            # Show help function
            show_help() {
              cat << EOF
Usage: opencode-client [COMMAND] [OPTIONS]

OpenCode client for conversation and history management.

Commands:
  send [MESSAGE]     Send message to current session (default)
  history [OPTIONS]  View conversation history
  sessions [OPTIONS] List available sessions
  help, --help       Show this help

Default behavior (no command): send "just say hi"

Examples:
  opencode-client "hello world"           # Send message (default)
  opencode-client send "hello world"     # Send message (explicit)
  opencode-client history                 # View current session history
  opencode-client sessions                # List sessions

Environment Variables:
  OPENCODE_URL          Server URL (default: http://127.0.0.1:4096)
  OPENCODE_PROJECT_DIR  Project directory (default: current directory)
  OPENCODE_PROVIDER     AI provider (optional)
  OPENCODE_MODEL        AI model (optional)
EOF
            }

            # Parse subcommand and arguments
            SUBCOMMAND=""
            ARGS=()

            # Handle help first
            if [[ "''${1:-}" == "help" || "''${1:-}" == "--help" || "''${1:-}" == "-h" ]]; then
              show_help
              exit 0
            fi

            # Parse first argument as potential subcommand
            case "''${1:-}" in
              "send"|"history"|"sessions")
                SUBCOMMAND="$1"
                shift
                ARGS=("$@")
                ;;
              "--history")
                # Compatibility alias
                SUBCOMMAND="history"
                shift
                ARGS=("$@")
                ;;
              "")
                # No args - default to send with default message
                SUBCOMMAND="send"
                ARGS=("just say hi")
                ;;
              *)
                # First arg is not a known subcommand - treat as send argument
                SUBCOMMAND="send"
                ARGS=("$@")
                ;;
            esac

            # Set up common variables
            OPENCODE_URL="''${OPENCODE_URL:-http://127.0.0.1:4096}"
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
            source "${./lib/session-helper.sh}"
            source "${./lib/history-helper.sh}"

            # Execute subcommand
            case "$SUBCOMMAND" in
              "send")
                MSG="''${ARGS[0]:-just say hi}"

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
                PAYLOAD=$(jq -n --arg text "$MSG" --arg p "$PROVIDER" --arg m "$MODEL" '
                  { parts: [{ type: "text", text: $text }] }
                  + (if $p != "" and $m != "" then { model: { providerID: $p, modelID: $m }} else {} end)
                ')

                # 4) Send message
                RESP=$(oc_session_http_post "$OPENCODE_URL/session/$SID/message" "$PAYLOAD")

                # 5) Extract response
                if echo "$RESP" | jq -e '.parts? // [] | length > 0' >/dev/null 2>&1; then
                  echo "[client] reply:" >&2 && echo "$RESP" | jq -r '(.parts[]? | select(.type=="text") | .text) // empty'
                else
                  echo "$RESP" | jq
                fi
                ;;

              "history")
                # Parse history options
                local session_id=""
                local format="text"
                local limit="20"

                # Parse arguments
                while [[ ''${#ARGS[@]} -gt 0 ]]; do
                  case "''${ARGS[0]}" in
                    --sid)
                      if [[ ''${#ARGS[@]} -lt 2 ]]; then
                        echo "[client] error: --sid requires a session ID" >&2
                        exit 1
                      fi
                      session_id="''${ARGS[1]}"
                      ARGS=("''${ARGS[@]:2}")
                      ;;
                    --format)
                      if [[ ''${#ARGS[@]} -lt 2 ]]; then
                        echo "[client] error: --format requires text or json" >&2
                        exit 1
                      fi
                      format="''${ARGS[1]}"
                      if [[ "$format" != "text" && "$format" != "json" ]]; then
                        echo "[client] error: --format must be 'text' or 'json'" >&2
                        exit 1
                      fi
                      ARGS=("''${ARGS[@]:2}")
                      ;;
                    --limit)
                      if [[ ''${#ARGS[@]} -lt 2 ]]; then
                        echo "[client] error: --limit requires a number" >&2
                        exit 1
                      fi
                      limit="''${ARGS[1]}"
                      ARGS=("''${ARGS[@]:2}")
                      ;;
                    *)
                      echo "[client] error: unknown option for history: ''${ARGS[0]}" >&2
                      echo "[hint] use: history [--sid SESSION_ID] [--format text|json] [--limit N]" >&2
                      exit 1
                      ;;
                  esac
                done

                # Health check
                if ! oc_session_http_get "$OPENCODE_URL/doc" >/dev/null; then
                  echo "[client] error: server not reachable at $OPENCODE_URL" >&2
                  echo "[hint] start: nix run nixpkgs#opencode -- serve --port 4096" >&2
                  exit 1
                fi

                # Auto-select session if not provided
                if [[ -z "$session_id" ]]; then
                  if session_id=$(oc_history_get_current_session_id "$PROJECT_DIR" "$OPENCODE_URL" 2>/dev/null); then
                    echo "[client] info: using current session: $session_id" >&2
                  else
                    echo "[client] error: no session found for this directory" >&2
                    echo "[hint] send a message first to create a session" >&2
                    exit 1
                  fi
                fi

                # Get and format messages
                local messages
                if messages=$(oc_history_get_messages "$session_id" "$limit" 2>/dev/null); then
                  case "$format" in
                    "text")
                      echo "$messages" | oc_history_format_text
                      ;;
                    "json")
                      echo "$messages" | oc_history_format_json
                      ;;
                  esac
                else
                  echo "[client] error: failed to retrieve history for session: $session_id" >&2
                  exit 1
                fi
                ;;

              "sessions")
                # Parse sessions options
                local target_dir="$PROJECT_DIR"
                local hostport=""
                local format="text"

                # Parse arguments
                while [[ ''${#ARGS[@]} -gt 0 ]]; do
                  case "''${ARGS[0]}" in
                    --dir)
                      if [[ ''${#ARGS[@]} -lt 2 ]]; then
                        echo "[client] error: --dir requires a directory path" >&2
                        exit 1
                      fi
                      target_dir="''${ARGS[1]}"
                      if [ ! -d "$target_dir" ]; then
                        echo "[client] error: directory not found: $target_dir" >&2
                        exit 1
                      fi
                      ARGS=("''${ARGS[@]:2}")
                      ;;
                    --hostport)
                      if [[ ''${#ARGS[@]} -lt 2 ]]; then
                        echo "[client] error: --hostport requires host:port format" >&2
                        exit 1
                      fi
                      hostport="''${ARGS[1]}"
                      ARGS=("''${ARGS[@]:2}")
                      ;;
                    --format)
                      if [[ ''${#ARGS[@]} -lt 2 ]]; then
                        echo "[client] error: --format requires text or json" >&2
                        exit 1
                      fi
                      format="''${ARGS[1]}"
                      if [[ "$format" != "text" && "$format" != "json" ]]; then
                        echo "[client] error: --format must be 'text' or 'json'" >&2
                        exit 1
                      fi
                      ARGS=("''${ARGS[@]:2}")
                      ;;
                    *)
                      echo "[client] error: unknown option for sessions: ''${ARGS[0]}" >&2
                      echo "[hint] use: sessions [--dir PATH] [--hostport HOST:PORT] [--format text|json]" >&2
                      exit 1
                      ;;
                  esac
                done

                # Health check (only needed for some index operations)
                if ! oc_session_http_get "$OPENCODE_URL/doc" >/dev/null; then
                  echo "[client] warning: server not reachable at $OPENCODE_URL, showing local cache only" >&2
                fi

                # Get normalized directory and hostport
                local normalized_dir
                if ! normalized_dir=$(oc_session_index_normalize_dir "$target_dir" 2>/dev/null); then
                  echo "[client] error: failed to normalize directory: $target_dir" >&2
                  exit 1
                fi

                local target_hostport="$hostport"
                if [[ -z "$target_hostport" ]]; then
                  if ! target_hostport=$(oc_session_index_normalize_hostport "$OPENCODE_URL" 2>/dev/null); then
                    echo "[client] error: failed to determine host:port from URL: $OPENCODE_URL" >&2
                    exit 1
                  fi
                fi

                # List sessions
                if [[ -n "$hostport" ]]; then
                  # Filter by specific hostport
                  echo "[client] info: listing sessions for host:port: $target_hostport" >&2
                  local dirs
                  if dirs=$(oc_session_index_list_dirs_by_hostport "$target_hostport" 2>/dev/null); then
                    if [[ "$format" == "json" ]]; then
                      echo "{"
                      echo "  \"hostport\": \"$target_hostport\","
                      echo "  \"directories\": ["
                      echo "$dirs" | while IFS= read -r dir; do
                        local sids
                        if sids=$(oc_session_index_list_sids_by_dir "$dir" 2>/dev/null); then
                          echo "    {"
                          echo "      \"directory\": \"$dir\","
                          echo "      \"sessions\": ["
                          echo "$sids" | while IFS= read -r sid; do
                            echo "        \"$sid\","
                          done | sed '$ s/,$//'
                          echo "      ]"
                          echo "    },"
                        fi
                      done | sed '$ s/,$//'
                      echo "  ]"
                      echo "}"
                    else
                      echo "Sessions for host:port: $target_hostport"
                      echo "$dirs" | while IFS= read -r dir; do
                        echo "Directory: $dir"
                        local sids
                        if sids=$(oc_session_index_list_sids_by_dir "$dir" 2>/dev/null); then
                          echo "$sids" | while IFS= read -r sid; do
                            echo "  📝 $sid"
                          done
                        else
                          echo "  (no sessions)"
                        fi
                        echo
                      done
                    fi
                  else
                    echo "[client] info: no sessions found for host:port: $target_hostport" >&2
                    if [[ "$format" == "json" ]]; then
                      echo '{"hostport": "'$target_hostport'", "directories": []}'
                    else
                      echo "No sessions found for host:port: $target_hostport"
                    fi
                  fi
                else
                  # List sessions for specific directory
                  echo "[client] info: listing sessions for directory: $normalized_dir" >&2
                  local sids
                  if sids=$(oc_session_index_list_sids_by_dir "$normalized_dir" 2>/dev/null); then
                    if [[ "$format" == "json" ]]; then
                      echo "{"
                      echo "  \"directory\": \"$normalized_dir\","
                      echo "  \"sessions\": ["
                      echo "$sids" | while IFS= read -r sid; do
                        echo "    \"$sid\","
                      done | sed '$ s/,$//'
                      echo "  ]"
                      echo "}"
                    else
                      echo "Sessions for directory: $normalized_dir"
                      echo "$sids" | while IFS= read -r sid; do
                        echo "📝 $sid"
                      done
                    fi
                  else
                    echo "[client] info: no sessions found for directory: $normalized_dir" >&2
                    if [[ "$format" == "json" ]]; then
                      echo '{"directory": "'$normalized_dir'", "sessions": []}'
                    else
                      echo "No sessions found for directory: $normalized_dir"
                      echo "Hint: Send a message first to create a session"
                    fi
                  fi
                fi
                ;;

              *)
                echo "[client] error: unknown subcommand: $SUBCOMMAND" >&2
                echo "[hint] run 'opencode-client --help' for usage" >&2
                exit 1
                ;;
            esac
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
