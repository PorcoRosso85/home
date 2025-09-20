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
    
    if curl -fsS --max-time "$timeout" -H 'Accept: application/json' "$@" "$url"; then
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
            echo "[client] error: invalid session ID in file: $session_file (sid=$existing_session). Remove the file or select another OPENCODE_PROJECT_DIR." >&2
            return 1
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

# ========================================
# Session Index Functions (Tier 0)
# ========================================

# Normalize directory path to absolute path without trailing slash
# Usage: oc_session_index_normalize_dir DIRECTORY_PATH
# stdout=normalized_path, stderr=log, exit 0=success
oc_session_index_normalize_dir() {
    local input_path="$1"

    if [[ -z "${input_path:-}" ]]; then
        echo "[oc_session_index_normalize_dir] error: empty path provided" >&2
        return 1
    fi

    # Resolve to absolute path
    local normalized
    if ! normalized=$(cd "$input_path" && pwd 2>/dev/null); then
        echo "[oc_session_index_normalize_dir] error: directory not found: $input_path" >&2
        return 1
    fi

    # Remove trailing slash
    normalized="${normalized%/}"

    echo "$normalized"
    return 0
}

# Normalize host:port from URL
# Usage: oc_session_index_normalize_hostport URL
# stdout=host:port, stderr=log, exit 0=success
oc_session_index_normalize_hostport() {
    local url="$1"

    if [[ -z "${url:-}" ]]; then
        echo "[oc_session_index_normalize_hostport] error: empty URL provided" >&2
        return 1
    fi

    # Remove protocol
    local host_port="${url#*://}"

    # Remove path
    host_port="${host_port%%/*}"

    # Validate host:port format
    if [[ ! "$host_port" =~ ^[^:]+:[0-9]+$ ]]; then
        echo "[oc_session_index_normalize_hostport] error: invalid host:port format: $host_port" >&2
        return 1
    fi

    echo "$host_port"
    return 0
}

# Generate directory hash (SHA256 prefix)
# Usage: oc_session_index_generate_dirhash DIRECTORY_PATH
# stdout=hash_prefix, stderr=log, exit 0=success
oc_session_index_generate_dirhash() {
    local dir_path="$1"

    if [[ -z "${dir_path:-}" ]]; then
        echo "[oc_session_index_generate_dirhash] error: empty path provided" >&2
        return 1
    fi

    # Generate SHA256 hash and take first 16 characters
    echo -n "$dir_path" | sha256sum | cut -c1-16
    return 0
}

# Get index file path
# Usage: oc_session_index_get_file_path
# stdout=index_file_path, stderr=log, exit 0=success
oc_session_index_get_file_path() {
    local session_base
    session_base=$(oc_session_get_base_dir)
    echo "$session_base/index.jsonl"
    return 0
}

# In-memory uniqueness tracking (process-scoped for Tier 0)
declare -A _OC_SESSION_INDEX_SEEN_KEYS

# Check if uniqueness key already exists (file-based check for persistence)
# Usage: oc_session_index_check_duplicate HOST_PORT DIR_HASH SESSION
# stdout=empty, stderr=log, exit 0=unique, exit 1=duplicate
oc_session_index_check_duplicate() {
    local hostPort="$1"
    local dirHash="$2"
    local session="$3"

    local uniqueness_key="${hostPort}|${dirHash}|${session}"

    # Check file-based duplicates first
    while IFS= read -r line; do
        if [[ -n "$line" ]]; then
            local record_hostPort record_dirHash record_session
            if record_hostPort=$(echo "$line" | jq -r '.hostPort' 2>/dev/null) && \
               record_dirHash=$(echo "$line" | jq -r '.dirHash' 2>/dev/null) && \
               record_session=$(echo "$line" | jq -r '.session' 2>/dev/null); then

                local existing_key="${record_hostPort}|${record_dirHash}|${record_session}"
                if [[ "$existing_key" == "$uniqueness_key" ]]; then
                    echo "[oc_session_index_check_duplicate] warning: duplicate key detected in file: $uniqueness_key" >&2
                    return 1
                fi
            fi
        fi
    done < <(oc_session_index_read_safe)

    # Also check in-memory (for current process efficiency)
    if [[ -n "${_OC_SESSION_INDEX_SEEN_KEYS[$uniqueness_key]:-}" ]]; then
        echo "[oc_session_index_check_duplicate] warning: duplicate key detected in memory: $uniqueness_key" >&2
        return 1
    fi

    # Mark as seen in memory
    _OC_SESSION_INDEX_SEEN_KEYS[$uniqueness_key]=1
    return 0
}

# Append new record to index with uniqueness check
# Usage: oc_session_index_append DIR HOST_PORT SESSION
# stdout=empty, stderr=log, exit 0=success
oc_session_index_append() {
    local dir="$1"
    local hostPort="$2"
    local session="$3"

    # Validate inputs
    if [[ -z "${dir:-}" || -z "${hostPort:-}" || -z "${session:-}" ]]; then
        echo "[oc_session_index_append] error: missing required parameters" >&2
        return 1
    fi

    # Normalize inputs
    local normalized_dir
    if ! normalized_dir=$(oc_session_index_normalize_dir "$dir"); then
        return 1
    fi

    local normalized_hostport
    if ! normalized_hostport=$(oc_session_index_normalize_hostport "$hostPort"); then
        return 1
    fi

    # Generate dirHash
    local dirHash
    if ! dirHash=$(oc_session_index_generate_dirhash "$normalized_dir"); then
        return 1
    fi

    # Check uniqueness
    if ! oc_session_index_check_duplicate "$normalized_hostport" "$dirHash" "$session"; then
        echo "[oc_session_index_append] error: duplicate record, skipping append" >&2
        return 1
    fi

    # Generate timestamp
    local created
    created=$(date +%s)

    # Create JSON record (compact for JSONL format)
    local json_record
    json_record=$(jq -n -c \
        --arg dir "$normalized_dir" \
        --arg dirHash "$dirHash" \
        --arg hostPort "$normalized_hostport" \
        --arg session "$session" \
        --arg created "$created" \
        '{dir: $dir, dirHash: $dirHash, hostPort: $hostPort, session: $session, created: $created}')

    # Get index file path
    local index_file
    if ! index_file=$(oc_session_index_get_file_path); then
        return 1
    fi

    # Ensure index directory exists
    mkdir -p "$(dirname "$index_file")"

    # Append record (Tier 0: simple append)
    echo "$json_record" >> "$index_file"

    echo "[oc_session_index_append] info: record appended: $session" >&2
    return 0
}

# Read all valid records, skip broken lines
# Usage: oc_session_index_read_safe
# stdout=json_records (one per line), stderr=log, exit 0=success
oc_session_index_read_safe() {
    local index_file
    if ! index_file=$(oc_session_index_get_file_path); then
        return 1
    fi

    if [[ ! -f "$index_file" ]]; then
        echo "[oc_session_index_read_safe] warning: index file not found: $index_file" >&2
        return 0
    fi

    local line_count=0
    local valid_count=0
    local broken_count=0

    while IFS= read -r line; do
        line_count=$((line_count + 1))

        if [[ -n "$line" ]] && echo "$line" | jq . >/dev/null 2>&1; then
            echo "$line"
            valid_count=$((valid_count + 1))
        else
            echo "[oc_session_index_read_safe] warning: skipping broken line $line_count" >&2
            broken_count=$((broken_count + 1))
        fi
    done < "$index_file"

    echo "[oc_session_index_read_safe] info: processed $line_count lines, $valid_count valid, $broken_count broken" >&2
    return 0
}

# Find record by session ID
# Usage: oc_session_index_lookup_by_sid SESSION_ID
# stdout=json_record (empty if not found), stderr=log, exit 0=success
oc_session_index_lookup_by_sid() {
    local session="$1"

    if [[ -z "${session:-}" ]]; then
        echo "[oc_session_index_lookup_by_sid] error: empty session ID provided" >&2
        return 1
    fi

    local found=0
    while IFS= read -r line; do
        if [[ -n "$line" ]]; then
            local record_session
            if record_session=$(echo "$line" | jq -r '.session' 2>/dev/null); then
                if [[ "$record_session" == "$session" ]]; then
                    echo "$line"
                    found=1
                    break
                fi
            fi
        fi
    done < <(oc_session_index_read_safe)

    if [[ $found -eq 0 ]]; then
        echo "[oc_session_index_lookup_by_sid] info: session not found: $session" >&2
    fi

    return 0
}

# ========================================
# Enhanced SID Reverse Lookup Functions (Step 4)
# ========================================

# Extract directory path from session ID
# Usage: oc_session_index_sid_to_dir SESSION_ID
# stdout=directory_path (empty if not found), stderr=log, exit 0=success
oc_session_index_sid_to_dir() {
    local session="$1"

    if [[ -z "${session:-}" ]]; then
        echo "[oc_session_index_sid_to_dir] error: empty session ID provided" >&2
        return 1
    fi

    local record
    if record=$(oc_session_index_lookup_by_sid "$session" 2>/dev/null); then
        if [[ -n "$record" ]]; then
            echo "$record" | jq -r '.dir' 2>/dev/null
            return 0
        fi
    fi

    echo "[oc_session_index_sid_to_dir] info: directory not found for session: $session" >&2
    return 0
}

# List all directories for a given host:port
# Usage: oc_session_index_list_dirs_by_hostport HOST_PORT
# stdout=directory_paths (one per line), stderr=log, exit 0=success
oc_session_index_list_dirs_by_hostport() {
    local hostPort="$1"

    if [[ -z "${hostPort:-}" ]]; then
        echo "[oc_session_index_list_dirs_by_hostport] error: empty host:port provided" >&2
        return 1
    fi

    local count=0
    while IFS= read -r line; do
        if [[ -n "$line" ]]; then
            local record_hostPort record_dir
            if record_hostPort=$(echo "$line" | jq -r '.hostPort' 2>/dev/null) &&
               record_dir=$(echo "$line" | jq -r '.dir' 2>/dev/null); then
                if [[ "$record_hostPort" == "$hostPort" ]]; then
                    echo "$record_dir"
                    count=$((count + 1))
                fi
            fi
        fi
    done < <(oc_session_index_read_safe)

    echo "[oc_session_index_list_dirs_by_hostport] info: found $count directories for $hostPort" >&2
    return 0
}

# List all session IDs for a given directory
# Usage: oc_session_index_list_sids_by_dir DIRECTORY_PATH
# stdout=session_ids (one per line), stderr=log, exit 0=success
oc_session_index_list_sids_by_dir() {
    local dir="$1"

    if [[ -z "${dir:-}" ]]; then
        echo "[oc_session_index_list_sids_by_dir] error: empty directory provided" >&2
        return 1
    fi

    # Normalize directory path for lookup (don't require directory to exist)
    local normalized_dir="$dir"
    # Remove trailing slash if present
    normalized_dir="${normalized_dir%/}"
    # Ensure absolute path
    if [[ ! "$normalized_dir" =~ ^/ ]]; then
        echo "[oc_session_index_list_sids_by_dir] error: directory must be absolute path: $dir" >&2
        return 1
    fi

    local count=0
    while IFS= read -r line; do
        if [[ -n "$line" ]]; then
            local record_dir record_session
            if record_dir=$(echo "$line" | jq -r '.dir' 2>/dev/null) &&
               record_session=$(echo "$line" | jq -r '.session' 2>/dev/null); then
                if [[ "$record_dir" == "$normalized_dir" ]]; then
                    echo "$record_session"
                    count=$((count + 1))
                fi
            fi
        fi
    done < <(oc_session_index_read_safe)

    echo "[oc_session_index_list_sids_by_dir] info: found $count sessions for $normalized_dir" >&2
    return 0
}

# Enhanced duplicate tracking with detailed statistics
# Usage: oc_session_index_get_duplicate_stats
# stdout=json_stats, stderr=log, exit 0=success
oc_session_index_get_duplicate_stats() {
    declare -A uniqueness_counts
    declare -A hostport_counts
    declare -A session_counts
    local total_records=0
    local duplicate_groups=0

    while IFS= read -r line; do
        if [[ -n "$line" ]]; then
            local hostPort dirHash session
            if hostPort=$(echo "$line" | jq -r '.hostPort' 2>/dev/null) &&
               dirHash=$(echo "$line" | jq -r '.dirHash' 2>/dev/null) &&
               session=$(echo "$line" | jq -r '.session' 2>/dev/null); then

                local uniqueness_key="${hostPort}|${dirHash}|${session}"
                uniqueness_counts[$uniqueness_key]=$((${uniqueness_counts[$uniqueness_key]:-0} + 1))
                hostport_counts[$hostPort]=$((${hostport_counts[$hostPort]:-0} + 1))
                session_counts[$session]=$((${session_counts[$session]:-0} + 1))
                total_records=$((total_records + 1))
            fi
        fi
    done < <(oc_session_index_read_safe)

    # Count duplicates
    for key in "${!uniqueness_counts[@]}"; do
        if [[ ${uniqueness_counts[$key]} -gt 1 ]]; then
            duplicate_groups=$((duplicate_groups + 1))
        fi
    done

    # Generate JSON stats
    local stats_json
    stats_json=$(jq -n \
        --arg total "$total_records" \
        --arg duplicates "$duplicate_groups" \
        --arg unique_hostports "${#hostport_counts[@]}" \
        --arg unique_sessions "${#session_counts[@]}" \
        '{
            totalRecords: $total | tonumber,
            duplicateGroups: $duplicates | tonumber,
            uniqueHostPorts: $unique_hostports | tonumber,
            uniqueSessions: $unique_sessions | tonumber
        }')

    echo "$stats_json"
    echo "[oc_session_index_get_duplicate_stats] info: analyzed $total_records records" >&2
    return 0
}

# Process-level session tracking integration
# Usage: oc_session_index_integrate_with_session DIR URL SESSION
# stdout=empty, stderr=log, exit 0=success
oc_session_index_integrate_with_session() {
    local dir="$1"
    local url="$2"
    local session="$3"

    if [[ -z "${dir:-}" || -z "${url:-}" || -z "${session:-}" ]]; then
        echo "[oc_session_index_integrate_with_session] error: missing required parameters" >&2
        return 1
    fi

    # Extract host:port from URL
    local hostPort
    if ! hostPort=$(oc_session_index_normalize_hostport "$url"); then
        return 1
    fi

    # Append to index (this will handle duplicates automatically)
    if oc_session_index_append "$dir" "$hostPort" "$session"; then
        echo "[oc_session_index_integrate_with_session] info: session integrated: $session" >&2
        return 0
    else
        echo "[oc_session_index_integrate_with_session] warning: session not appended (likely duplicate): $session" >&2
        return 0  # Don't fail on duplicates
    fi
}

# ========================================
# Index Rebuild and Recovery Functions (Step 5)
# ========================================

# Scan existing session files and rebuild index
# Usage: oc_session_index_rebuild [--dry-run]
# stdout=rebuild_summary, stderr=log, exit 0=success
oc_session_index_rebuild() {
    local dry_run=false
    if [[ "${1:-}" == "--dry-run" ]]; then
        dry_run=true
        echo "[oc_session_index_rebuild] info: running in dry-run mode" >&2
    fi

    local session_base
    session_base=$(oc_session_get_base_dir)

    echo "[oc_session_index_rebuild] info: scanning session files in $session_base" >&2

    local rebuild_count=0
    local error_count=0
    local temp_index=""

    if [[ "$dry_run" == false ]]; then
        # Create temporary index file
        temp_index=$(mktemp "${session_base}/index.jsonl.rebuild.XXXXXX")
        echo "[oc_session_index_rebuild] info: using temp file: $temp_index" >&2
    fi

    # Scan all session files (use process substitution to avoid subshell variable issues)
    while IFS= read -r session_file; do
        echo "[oc_session_index_rebuild] info: processing $session_file" >&2

        # Extract directory and host:port from session file path
        local relative_path="${session_file#"$session_base"/}"
        local hostport="${relative_path%%/*}"
        local project_file="${relative_path#*/}"
        local project_key="${project_file%.session}"

        # Convert project key back to directory path
        local dir_path
        dir_path=$(echo "$project_key" | sed 's/__SLASH__/\//g')
        if [[ ! "$dir_path" =~ ^/ ]]; then
            dir_path="/$dir_path"
        fi

        # Read session ID from file
        local session_id
        if session_id=$(cat "$session_file" 2>/dev/null); then
            if [[ -n "$session_id" ]]; then
                echo "[oc_session_index_rebuild] info: found session $session_id for $dir_path" >&2

                if [[ "$dry_run" == false ]]; then
                    # Generate index record
                    local dirHash
                    dirHash=$(oc_session_index_generate_dirhash "$dir_path")
                    local created
                    created=$(stat -c %Y "$session_file" 2>/dev/null || date +%s)

                    local json_record
                    json_record=$(jq -n -c \
                        --arg dir "$dir_path" \
                        --arg dirHash "$dirHash" \
                        --arg hostPort "$hostport" \
                        --arg session "$session_id" \
                        --arg created "$created" \
                        '{dir: $dir, dirHash: $dirHash, hostPort: $hostPort, session: $session, created: $created}')

                    echo "$json_record" >> "$temp_index"
                fi

                rebuild_count=$((rebuild_count + 1))
            else
                echo "[oc_session_index_rebuild] warning: empty session file: $session_file" >&2
                error_count=$((error_count + 1))
            fi
        else
            echo "[oc_session_index_rebuild] warning: cannot read session file: $session_file" >&2
            error_count=$((error_count + 1))
        fi
    done < <(find "$session_base" -name "*.session" -type f 2>/dev/null)

    if [[ "$dry_run" == false ]] && [[ -f "$temp_index" ]]; then
        # Replace existing index with rebuilt one
        local index_file
        index_file=$(oc_session_index_get_file_path)

        # Backup existing index if it exists
        if [[ -f "$index_file" ]]; then
            local backup_file="${index_file}.backup.$(date +%s)"
            cp "$index_file" "$backup_file"
            echo "[oc_session_index_rebuild] info: backed up existing index to $backup_file" >&2
        fi

        # Replace with rebuilt index
        mv "$temp_index" "$index_file"
        echo "[oc_session_index_rebuild] info: index rebuilt successfully" >&2
    fi

    # Generate summary
    local summary
    summary=$(jq -n \
        --arg mode "$(if $dry_run; then echo "dry-run"; else echo "rebuild"; fi)" \
        --arg rebuilt "$rebuild_count" \
        --arg errors "$error_count" \
        '{mode: $mode, rebuiltRecords: $rebuilt | tonumber, errorCount: $errors | tonumber}')

    echo "$summary"
    echo "[oc_session_index_rebuild] info: rebuild complete - $rebuild_count records, $error_count errors" >&2
    return 0
}

# Validate index consistency against session files
# Usage: oc_session_index_validate
# stdout=validation_report, stderr=log, exit 0=success
oc_session_index_validate() {
    echo "[oc_session_index_validate] info: validating index consistency" >&2

    local session_base
    session_base=$(oc_session_get_base_dir)

    declare -A index_sessions
    declare -A file_sessions

    # Read index records
    while IFS= read -r line; do
        if [[ -n "$line" ]]; then
            local session hostPort dir
            if session=$(echo "$line" | jq -r '.session' 2>/dev/null) &&
               hostPort=$(echo "$line" | jq -r '.hostPort' 2>/dev/null) &&
               dir=$(echo "$line" | jq -r '.dir' 2>/dev/null); then
                index_sessions["$session"]="$hostPort|$dir"
            fi
        fi
    done < <(oc_session_index_read_safe)

    # Read session files (use process substitution to avoid subshell variable issues)
    while IFS= read -r session_file; do
        local session_id
        if session_id=$(cat "$session_file" 2>/dev/null); then
            if [[ -n "$session_id" ]]; then
                # Extract metadata from file path
                local relative_path="${session_file#"$session_base"/}"
                local hostport="${relative_path%%/*}"
                local project_file="${relative_path#*/}"
                local project_key="${project_file%.session}"
                local dir_path
                dir_path=$(echo "$project_key" | sed 's/__SLASH__/\//g')
                if [[ ! "$dir_path" =~ ^/ ]]; then
                    dir_path="/$dir_path"
                fi

                file_sessions["$session_id"]="$hostport|$dir_path"
            fi
        fi
    done < <(find "$session_base" -name "*.session" -type f 2>/dev/null)

    # Check for mismatches
    local missing_in_index=0
    local missing_in_files=0
    local mismatched=0

    # Check index sessions against files
    for session in "${!index_sessions[@]}"; do
        if [[ -z "${file_sessions[$session]:-}" ]]; then
            echo "[oc_session_index_validate] warning: session in index but not in files: $session" >&2
            missing_in_files=$((missing_in_files + 1))
        elif [[ "${index_sessions[$session]}" != "${file_sessions[$session]}" ]]; then
            echo "[oc_session_index_validate] warning: metadata mismatch for $session" >&2
            echo "  Index: ${index_sessions[$session]}" >&2
            echo "  Files: ${file_sessions[$session]}" >&2
            mismatched=$((mismatched + 1))
        fi
    done

    # Check file sessions against index
    for session in "${!file_sessions[@]}"; do
        if [[ -z "${index_sessions[$session]:-}" ]]; then
            echo "[oc_session_index_validate] warning: session in files but not in index: $session" >&2
            missing_in_index=$((missing_in_index + 1))
        fi
    done

    # Generate validation report
    local report
    report=$(jq -n \
        --arg index_count "${#index_sessions[@]}" \
        --arg file_count "${#file_sessions[@]}" \
        --arg missing_in_index "$missing_in_index" \
        --arg missing_in_files "$missing_in_files" \
        --arg mismatched "$mismatched" \
        '{
            indexRecords: $index_count | tonumber,
            fileRecords: $file_count | tonumber,
            missingInIndex: $missing_in_index | tonumber,
            missingInFiles: $missing_in_files | tonumber,
            mismatched: $mismatched | tonumber,
            isConsistent: (($missing_in_index | tonumber) + ($missing_in_files | tonumber) + ($mismatched | tonumber)) == 0
        }')

    echo "$report"

    local total_issues
    total_issues=$((missing_in_index + missing_in_files + mismatched))
    echo "[oc_session_index_validate] info: validation complete - $total_issues issues found" >&2

    return 0
}