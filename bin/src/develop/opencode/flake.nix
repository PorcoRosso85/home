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
            shellcheck  # For shell script quality testing
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
  status [--probe]   Quick diagnostic check (--probe: test send capability)
  ps                 Discover running OpenCode servers and show connection URLs
  help, --help       Show this help

Default behavior (no command): send "just say hi"

Examples:
  opencode-client "hello world"           # Send message (default)
  opencode-client send "hello world"     # Send message (explicit)
  opencode-client history                 # View current session history
  opencode-client sessions                # List sessions
  opencode-client status                  # Quick diagnostic check
  opencode-client status --probe          # Test send capability with structured errors

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
              "send"|"history"|"sessions"|"status"|"ps")
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
            source "${./lib/diagnostic-helper.sh}"
            source "${./lib/process-discovery.sh}"

            # Execute subcommand
            case "$SUBCOMMAND" in
              "send")
                MSG="''${ARGS[0]:-just say hi}"

                # 1) Health check (OpenAPI doc)
                if ! oc_session_http_get "$OPENCODE_URL/doc" >/dev/null; then
                  echo "[client] error: server not reachable at $OPENCODE_URL" >&2
                  oc_diag_next_connection_help "$OPENCODE_URL"
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

                # 4) Send message with enhanced error handling
                echo "[debug] Sending message to session $SID..." >&2
                RESP=$(oc_session_http_post "$OPENCODE_URL/session/$SID/message" "$PAYLOAD")
                POST_EXIT_CODE=$?
                echo "[debug] POST exit code: $POST_EXIT_CODE" >&2
                echo "[debug] Response: $RESP" >&2

                # 5) Enhanced response handling with structured error messages
                echo "[debug] Starting response analysis..." >&2
                if [[ $POST_EXIT_CODE -eq 0 ]]; then
                  echo "[debug] POST was successful (exit 0)" >&2
                  # Message sent successfully, check for immediate error or wait for response
                  if echo "$RESP" | jq -e '.name == "ProviderModelNotFoundError"' >/dev/null 2>&1; then
                    echo "[debug] ProviderModelNotFoundError detected" >&2
                    # Immediate error response from server
                    ERROR_DATA=$(echo "$RESP" | jq -r '.data // {}' 2>/dev/null || echo "{}")
                    PROVIDER_ID=$(echo "$ERROR_DATA" | jq -r '.providerID // "unknown"' 2>/dev/null)
                    MODEL_ID=$(echo "$ERROR_DATA" | jq -r '.modelID // "unknown"' 2>/dev/null)

                    echo "[Error] ProviderModelNotFoundError: $PROVIDER_ID/$MODEL_ID not available" >&2

                    # Get available providers
                    oc_diag_show_available "$OPENCODE_URL"

                    echo "[Fix] OPENCODE_PROVIDER=opencode OPENCODE_MODEL=grok-code nix run .#opencode-client -- 'test'" >&2
                    echo "[Help] See docs/TROUBLESHOOTING-TUI-HTTP-API.md" >&2
                    exit 1
                  elif echo "$RESP" | jq -e '.parts? // [] | length > 0' >/dev/null 2>&1; then
                    # Success: Extract and display response
                    echo "[client] reply:" >&2 && echo "$RESP" | jq -r '(.parts[]? | select(.type=="text") | .text) // empty'
                  else
                    # Message sent but no immediate response, wait for assistant response
                    echo "[client] waiting for response..." >&2

                    # Poll for assistant response (with timeout)
                    for attempt in {1..15}; do
                      sleep 1
                      MESSAGES=$(curl -s "$OPENCODE_URL/session/$SID/message" 2>/dev/null | jq '.[-2:]' 2>/dev/null || echo '[]')

                      # Check if we have an assistant response
                      ASSISTANT_MSG=$(echo "$MESSAGES" | jq '.[] | select(.info.role == "assistant")' 2>/dev/null | tail -1)

                      if [[ -n "$ASSISTANT_MSG" ]]; then
                        # Got assistant response
                        ASSISTANT_TEXT=$(echo "$ASSISTANT_MSG" | jq -r '.parts[]? | select(.type=="text") | .text' 2>/dev/null || echo "")
                        if [[ -n "$ASSISTANT_TEXT" ]]; then
                          echo "[client] reply:" >&2 && echo "$ASSISTANT_TEXT"
                          exit 0
                        fi
                      fi
                    done

                    # Timeout - no assistant response
                    echo "[client] timeout: no assistant response received" >&2
                    echo "[Help] This may indicate a model configuration issue. Try: ./check-opencode-status.sh" >&2
                    exit 1
                  fi
                elif [[ $POST_EXIT_CODE -ne 0 ]] && echo "$RESP" | grep -q "HTTP POST failed"; then
                  # HTTP error: Provide structured error message
                  echo "[Error] Request failed. Analyzing error..." >&2

                  # Try to get detailed error from server
                  DETAILED_ERROR=$(curl -s -X POST "$OPENCODE_URL/session/$SID/message" \
                    -H 'Content-Type: application/json' \
                    -d "$PAYLOAD" 2>&1 || echo '{"name":"UnknownError"}')

                  # Parse error type
                  ERROR_TYPE=$(echo "$DETAILED_ERROR" | jq -r '.name // "UnknownError"' 2>/dev/null || echo "UnknownError")
                  ERROR_DATA=$(echo "$DETAILED_ERROR" | jq -r '.data // {}' 2>/dev/null || echo "{}")

                  if [[ "$ERROR_TYPE" == "ProviderModelNotFoundError" ]]; then
                    # Specific error: ProviderModelNotFoundError
                    PROVIDER_ID=$(echo "$ERROR_DATA" | jq -r '.providerID // "unknown"' 2>/dev/null)
                    MODEL_ID=$(echo "$ERROR_DATA" | jq -r '.modelID // "unknown"' 2>/dev/null)

                    echo "[Error] ProviderModelNotFoundError: $PROVIDER_ID/$MODEL_ID not available" >&2

                    # Get available providers
                    oc_diag_show_available "$OPENCODE_URL"

                    echo "[Fix] OPENCODE_PROVIDER=opencode OPENCODE_MODEL=grok-code nix run .#opencode-client -- 'test'" >&2
                    echo "[Help] See docs/TROUBLESHOOTING-TUI-HTTP-API.md" >&2
                  else
                    # Generic error: Show available providers
                    echo "[Error] Request failed. Checking available providers..." >&2

                    oc_diag_show_available "$OPENCODE_URL"

                    echo "[Fix] Set provider: OPENCODE_PROVIDER=opencode OPENCODE_MODEL=grok-code" >&2
                    echo "[Help] Use ./check-opencode-status.sh for detailed diagnosis" >&2
                  fi
                  exit 1
                else
                  # Fallback: Show raw response for debugging
                  echo "$RESP" | jq 2>/dev/null || echo "$RESP"
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
                  oc_diag_next_connection_help "$OPENCODE_URL"
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

              "status")
                # Parse status options
                probe_mode="false"

                # Parse arguments
                while [[ ''${#ARGS[@]} -gt 0 ]]; do
                  case "''${ARGS[0]}" in
                    --probe)
                      probe_mode="true"
                      ARGS=("''${ARGS[@]:1}")
                      ;;
                    *)
                      echo "[client] error: unknown option for status: ''${ARGS[0]}" >&2
                      echo "[hint] use: status [--probe]" >&2
                      exit 1
                      ;;
                  esac
                done

                if [[ "$probe_mode" == "true" ]]; then
                  # Lightweight probe mode
                  echo "[client] 🧪 Probing send capability..." >&2

                  # Quick server check
                  if ! oc_session_http_get "$OPENCODE_URL/doc" >/dev/null 2>&1; then
                    echo >&2
                    echo "[Error] Server not reachable at $OPENCODE_URL" >&2
                    echo "[Available] Check server status with: curl -s $OPENCODE_URL/doc" >&2
                    oc_diag_next_start_server
                    oc_diag_next_full_diagnosis
                    exit 1
                  fi

                  # Quick send test
                  TEST_SID=$(oc_session_get_or_create "$OPENCODE_URL" "$PROJECT_DIR" 2>/dev/null)
                  if [[ -n "$TEST_SID" ]]; then
                    # Try sending a minimal probe message
                    PROBE_RESP=$(oc_session_http_post "$OPENCODE_URL/session/$TEST_SID/message" \
                      '{"parts":[{"type":"text","text":"probe"}]}' 2>/dev/null)
                    PROBE_EXIT=$?

                    if [[ $PROBE_EXIT -eq 0 ]]; then
                      echo "[client] ✅ OK: send probe succeeded" >&2
                      exit 0
                    else
                      echo >&2
                      echo "[Error] Message sending failed" >&2

                      # Get available providers for structured error
                      oc_diag_show_available "$OPENCODE_URL"
                      echo "[Fix] Try: OPENCODE_PROVIDER=opencode OPENCODE_MODEL=grok-code" >&2
                      echo "[Help] Full diagnosis: ./check-opencode-status.sh" >&2
                      exit 1
                    fi
                  else
                    echo >&2
                    echo "[Error] Session creation failed" >&2
                    echo "[Available] Check server configuration" >&2
                    echo "[Fix] Verify server: curl -s $OPENCODE_URL/config/providers" >&2
                    echo "[Help] Full diagnosis: ./check-opencode-status.sh" >&2
                    exit 1
                  fi
                else
                  # Regular status mode
                  echo "[client] OpenCode Status Check" >&2
                  echo "[client] ===================" >&2
                  echo >&2
                fi

                # Check 1: Server connectivity
                echo "[client] 🖥️  Server Status:" >&2
                if oc_session_http_get "$OPENCODE_URL/doc" >/dev/null 2>&1; then
                  echo "[client]   ✅ Server online at $OPENCODE_URL" >&2

                  # Get available providers
                  PROVIDERS=$(curl -s "$OPENCODE_URL/config/providers" 2>/dev/null | \
                    jq -r '.providers[].id' 2>/dev/null | tr '\n' ', ' | sed 's/,$//' || echo "unknown")
                  echo "[client]   📋 HTTP API Providers: $PROVIDERS" >&2
                else
                  echo "[client]   ❌ Server offline at $OPENCODE_URL" >&2
                  oc_diag_next_start_server
                  exit 1
                fi
                echo >&2

                # Check 2: Project directory
                echo "[client] 📁 Project Directory:" >&2
                echo "[client]   📍 OPENCODE_PROJECT_DIR: $PROJECT_DIR" >&2
                if [[ -d "$PROJECT_DIR" ]]; then
                  echo "[client]   ✅ Directory exists" >&2
                else
                  echo "[client]   ❌ Directory not found" >&2
                fi
                echo >&2

                # Check 3: Session status
                echo "[client] 🔗 Session Status:" >&2
                if SID=$(oc_session_get_current_session_id "$PROJECT_DIR" "$OPENCODE_URL" 2>/dev/null); then
                  echo "[client]   ✅ Active session: $SID" >&2
                else
                  echo "[client]   📝 No active session (will create new)" >&2
                fi
                echo >&2

                # Check 4: Quick connectivity test
                echo "[client] 🧪 Connectivity Test:" >&2
                echo "[client]   📤 Sending test message..." >&2
                TEST_SID=$(oc_session_get_or_create "$OPENCODE_URL" "$PROJECT_DIR" 2>/dev/null)
                if [[ -n "$TEST_SID" ]]; then
                  echo "[client]   ✅ Session creation successful" >&2
                  echo "[client]   🆔 Test session: $TEST_SID" >&2
                else
                  echo "[client]   ❌ Session creation failed" >&2
                fi
                echo >&2

                # Summary and recommendations
                echo "[client] 📋 Quick Actions:" >&2
                echo "[client]   • Send message: OPENCODE_PROJECT_DIR=\$(pwd) nix run .#opencode-client -- 'hello'" >&2
                echo "[client]   • View history: OPENCODE_PROJECT_DIR=\$(pwd) nix run .#opencode-client -- history" >&2
                echo "[client]   • Full diagnosis: ./check-opencode-status.sh" >&2
                ;;

              "ps")
                # Process discovery subcommand - find running OpenCode servers
                echo "[client] Discovering OpenCode servers..." >&2

                # Discover servers using OS-compatible process discovery
                servers_json=$(oc_ps_discover_servers 2>/dev/null)
                if [[ $? -eq 0 && -n "$servers_json" ]]; then
                  # Generate export commands and guidance
                  if oc_ps_generate_exports "$servers_json"; then
                    exit 0  # Success with guidance
                  else
                    exit 1  # No reachable servers found
                  fi
                else
                  echo "[Error] Process discovery failed" >&2
                  echo "[Help] Check system permissions or try manual server start:" >&2
                  oc_diag_next_start_server
                  exit 1
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
