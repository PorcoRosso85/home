#!/usr/bin/env bash
# OpenCode History Helper
# Conversation history retrieval and formatting functions

# Usage: oc_history_get_messages SESSION_ID [LIMIT]
# stdout=json_messages_array, stderr=log, exit 0=success
oc_history_get_messages() {
    local session_id="$1"
    local limit="${2:-20}"

    if [[ -z "${session_id:-}" ]]; then
        echo "[oc_history_get_messages] error: empty session ID provided" >&2
        return 1
    fi

    # Use session helper's HTTP function (assumes OPENCODE_URL is set)
    local url="${OPENCODE_URL:-http://127.0.0.1:4096}"

    echo "[oc_history_get_messages] info: fetching messages for session: $session_id" >&2

    # Try to get messages from API
    if ! oc_session_http_get "$url/session/$session_id/message" 2>/dev/null; then
        echo "[oc_history_get_messages] error: failed to fetch messages for session: $session_id" >&2
        echo "[]"  # Return empty array on failure
        return 1
    fi
}

# Usage: oc_history_format_text < JSON_ARRAY
# stdout=human_readable_text, stderr=log, exit 0=success
oc_history_format_text() {
    local json_input
    json_input=$(cat)

    if [[ -z "$json_input" || "$json_input" == "[]" ]]; then
        echo "[oc_history_format_text] info: no messages to format" >&2
        echo "No messages found."
        return 0
    fi

    echo "[oc_history_format_text] info: formatting messages as text" >&2

    # Format messages for human reading
    echo "$json_input" | jq -r '
        .[] |
        if .info.type == "user" then
            "🗣️  User: " + (.parts[]? | select(.type=="text") | .text)
        elif .info.type == "assistant" then
            "🤖 Assistant: " + (.parts[]? | select(.type=="text") | .text)
        else
            "📝 " + (.info.type // "unknown") + ": " + (.parts[]? | select(.type=="text") | .text // "No text content")
        end
    ' 2>/dev/null || {
        echo "[oc_history_format_text] error: failed to parse JSON input" >&2
        echo "Error: Invalid message format"
        return 1
    }
}

# Usage: oc_history_format_json < JSON_ARRAY
# stdout=formatted_json, stderr=log, exit 0=success
oc_history_format_json() {
    local json_input
    json_input=$(cat)

    if [[ -z "$json_input" || "$json_input" == "[]" ]]; then
        echo "[oc_history_format_json] info: no messages to format" >&2
        echo "[]"
        return 0
    fi

    echo "[oc_history_format_json] info: formatting messages as JSON" >&2

    # Pretty-print JSON with jq
    echo "$json_input" | jq '.' 2>/dev/null || {
        echo "[oc_history_format_json] error: failed to parse JSON input" >&2
        echo "{\"error\": \"Invalid JSON format\"}"
        return 1
    }
}

# Usage: oc_history_get_current_session_id PROJECT_DIR [URL]
# stdout=session_id, stderr=log, exit 0=success
oc_history_get_current_session_id() {
    local project_dir="$1"
    local url="${2:-${OPENCODE_URL:-http://127.0.0.1:4096}}"

    if [[ -z "${project_dir:-}" ]]; then
        echo "[oc_history_get_current_session_id] error: empty project directory provided" >&2
        return 1
    fi

    # Use session helper to get session file path
    local session_file
    session_file=$(oc_session_get_file_path "$url" "$project_dir" 2>/dev/null) || {
        echo "[oc_history_get_current_session_id] error: failed to determine session file path" >&2
        return 1
    }

    # Get existing session ID
    local session_id
    session_id=$(oc_session_get_existing_id "$session_file" 2>/dev/null) || {
        echo "[oc_history_get_current_session_id] error: no existing session found" >&2
        return 1
    }

    if [[ -z "$session_id" ]]; then
        echo "[oc_history_get_current_session_id] error: session file exists but is empty" >&2
        return 1
    fi

    echo "$session_id"
}