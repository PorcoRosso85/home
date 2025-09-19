#!/usr/bin/env bash
# OpenCode Session Management Helper Functions  
# Unified functions for directory-based session continuity
# Compliant with conventions/prohibited_items.md (no flake.nix shell implementations)

set -euo pipefail

# Environment variable resolution order: OPENCODE_SESSION_DIR → XDG_STATE_HOME → default
oc_session_get_base_dir() {
    if [[ -n "${OPENCODE_SESSION_DIR:-}" ]]; then
        echo "${OPENCODE_SESSION_DIR}/opencode/sessions"
    else
        local state_base="${XDG_STATE_HOME:-$HOME/.local/state}"
        echo "$state_base/opencode/sessions"
    fi
}

# Normalize URL (internal utility, consistent behavior)
oc_session_normalize_url() {
    local url="$1"
    echo "${url%/}"
}

# Derive host:port from URL (internal utility, DIP compliance)
oc_session_derive_host_port() {
    local url="$1"
    local host_port="${url#*://}"
    host_port="${host_port%%/*}"
    echo "$host_port"
}

# Convert absolute path to project key (DRY principle)
# Usage: oc_session_project_key ABSOLUTE_PATH
# Converts /path/to/project → path__SLASH__to__SLASH__project
# Fixed: Uses __SLASH__ delimiter to prevent underscore collisions
#
# Examples:
#   /sops_flake     → sops_flake
#   /sops/flake     → sops__SLASH__flake
#   /my_project     → my_project
#   /my/project     → my__SLASH__project
oc_session_project_key() {
    local abs_path="$1"

    # Input validation
    if [[ -z "${abs_path:-}" ]]; then
        echo "[error] oc_session_project_key: empty path provided" >&2
        return 1
    fi

    # Convert slashes to safe delimiter and remove leading delimiter
    echo "$abs_path" | sed 's/\//__SLASH__/g' | sed 's/^__SLASH__//'
}

# HTTP GET request with unified options and timeout (DRY principle)
# Usage: oc_session_http_get URL [additional_curl_options...]
# stdout=response body, stderr=error messages, exit 0=success
oc_session_http_get() {
    local url="$1"
    shift
    local timeout="${OPENCODE_TIMEOUT:-30}"
    
    if curl -fsS --max-time "$timeout" "$@" "$url"; then
        return 0
    else
        echo "[error] HTTP GET failed: $url" >&2
        return 1
    fi
}

# HTTP POST request with JSON content-type and unified options (DRY principle)
# Usage: oc_session_http_post URL JSON_DATA [additional_curl_options...]
# stdout=response body, stderr=error messages, exit 0=success
oc_session_http_post() {
    local url="$1"
    local json_data="$2"
    shift 2
    local timeout="${OPENCODE_TIMEOUT:-30}"
    
    if curl -fsS --max-time "$timeout" \
        -X POST \
        -H 'Content-Type: application/json' \
        -d "$json_data" \
        "$@" \
        "$url"; then
        return 0
    else
        echo "[error] HTTP POST failed: $url" >&2
        return 1
    fi
}

# Get session file path for directory (main path resolution function)
oc_session_get_file_path() {
    local url="$1"
    local workdir="${2:-$(pwd)}"
    
    url=$(oc_session_normalize_url "$url")
    local hostport
    hostport=$(oc_session_derive_host_port "$url")
    
    # Convert absolute path to safe filename
    local abs_path
    if ! abs_path=$(cd "$workdir" && pwd) 2>/dev/null; then
        echo "[error] Directory not found: $workdir" >&2
        return 1
    fi
    local project_name
    project_name=$(oc_session_project_key "$abs_path")
    
    local session_base
    session_base=$(oc_session_get_base_dir)
    echo "$session_base/$hostport/$project_name.session"
}

# Validate session via API (URL-only dependency for DIP compliance)
oc_session_validate_api() {
    local url="$1"
    local session_id="$2"
    
    if oc_session_http_get "$url/session/$session_id" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Get existing session ID from file
oc_session_get_existing_id() {
    local session_file="$1"
    
    if [[ -f "$session_file" ]]; then
        cat "$session_file" 2>/dev/null || echo ""
    else
        echo ""
    fi
}

# Save session ID to file
oc_session_save_id() {
    local session_file="$1"
    local session_id="$2"
    
    mkdir -p "$(dirname "$session_file")"
    echo "$session_id" > "$session_file"
}

# Main function: Get or create session with directory-based continuity
# stdout=session_id, stderr=log messages (machine readable / human readable separation)
oc_session_get_or_create() {
    local url="$1"
    local workdir="${2:-$(pwd)}"
    
    url=$(oc_session_normalize_url "$url")
    
    # Initialize session directories
    local session_base
    session_base=$(oc_session_get_base_dir)
    mkdir -p "$session_base"
    
    local session_file
    session_file=$(oc_session_get_file_path "$url" "$workdir")
    
    # Check existing session
    local existing_session
    existing_session=$(oc_session_get_existing_id "$session_file")
    
    if [[ -n "$existing_session" ]]; then
        if oc_session_validate_api "$url" "$existing_session" 2>/dev/null; then
            echo "[client] session: $existing_session (resumed)" >&2
            echo "$existing_session"
            return 0
        else
            echo "[client] session: invalid session found, creating new one" >&2
        fi
    fi
    
    # Create new session via API
    local new_session
    if new_session=$(oc_session_http_post "$url/session" '{}' | jq -r '.id' 2>/dev/null); then
        
        if [[ -n "$new_session" && "$new_session" != "null" ]]; then
            oc_session_save_id "$session_file" "$new_session"
            echo "[client] session: $new_session (new)" >&2
            echo "$new_session"
            return 0
        fi
    fi
    
    # Failed to create session
    echo "[client] error: failed to create session" >&2
    return 1
}