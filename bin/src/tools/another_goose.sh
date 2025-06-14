#!/usr/bin/env bash
set -e

# @describe Set AI provider and model for goose, then execute with the provided parameters.
# @option --provider=openrouter The AI provider to use (指定がない場合: "openrouter").
# @option --model=deepseek/deepseek-chat-v3-0324 The model to use (指定がない場合: "deepseek/deepseek-chat-v3-0324").
# @option --with-builtin=developer The built-in tool to use with goose (指定がない場合: "developer").
# @option --text The text prompt to send to the AI model.

# @env LLM_OUTPUT=/dev/stdout The output path

# Fix path resolution without using realpath
get_abs_path() {
    local path="$1"
    if [[ "$path" = /* ]]; then
        echo "$path"
    else
        echo "$(cd "$(dirname "$path")" && pwd)/$(basename "$path")"
    fi
}

script_path=$(get_abs_path "${BASH_SOURCE[0]}")
script_dir=$(dirname "$script_path")
ROOT_DIR="${LLM_ROOT_DIR:-$(cd "$script_dir/.." && pwd)}"

main() {
    # Check for guard_operation.sh but continue if it doesn't exist
    if [[ -f "$ROOT_DIR/utils/guard_operation.sh" ]]; then
        "$ROOT_DIR/utils/guard_operation.sh"
    else
        echo "Warning: guard_operation.sh not found, continuing without it" >> "$LLM_OUTPUT" 
    fi
    
    # Load secret environment variables
    if [ -f "$HOME/secret.sh" ]; then
        source "$HOME/secret.sh" >> "$LLM_OUTPUT" 2>&1 || {
            echo "Error: Failed to source $HOME/secret.sh" >> "$LLM_OUTPUT"
            return 1
        }
    else
        echo "Warning: $HOME/secret.sh not found, continuing without it" >> "$LLM_OUTPUT"
    fi
    
    # Find the goose executable - try multiple locations
    if command -v goose > /dev/null 2>&1; then
        GOOSE_CMD=$(command -v goose)
    elif [ -x "/usr/bin/goose" ]; then
        GOOSE_CMD="/usr/bin/goose"
    elif [ -x "/usr/local/bin/goose" ]; then
        GOOSE_CMD="/usr/local/bin/goose"
    elif [ -x "$HOME/.local/bin/goose" ]; then
        GOOSE_CMD="$HOME/.local/bin/goose"
    elif [ -x "$HOME/.nix-profile/bin/goose" ]; then
        GOOSE_CMD="$HOME/.nix-profile/bin/goose"
    else
        echo "Error: goose command not found in PATH or common locations" >> "$LLM_OUTPUT"
        return 1
    fi
    
    echo "Using goose at: $GOOSE_CMD" >> "$LLM_OUTPUT"
    
    # Set provider and model
    export GOOSE_PROVIDER="$argc_provider"
    export GOOSE_MODEL="$argc_model"
    
    echo "Set GOOSE_PROVIDER=$GOOSE_PROVIDER" >> "$LLM_OUTPUT"
    echo "Set GOOSE_MODEL=$GOOSE_MODEL" >> "$LLM_OUTPUT"
    
    # Set RUST_BACKTRACE environment variable
    export RUST_BACKTRACE=1
    
    # Build command with optional parameters
    cmd="$GOOSE_CMD run"
    
    # Add --with-builtin parameter if provided
    if [ -n "$argc_with_builtin" ]; then
        cmd="$cmd --with-builtin $argc_with_builtin"
        echo "With built-in tool: $argc_with_builtin" >> "$LLM_OUTPUT"
    fi
    
    # Add --text parameter if provided
    if [ -n "$argc_text" ]; then
        cmd="$cmd --text \"$argc_text\""
        echo "With text: $argc_text" >> "$LLM_OUTPUT"
    fi
    
    echo "Executing: $cmd" >> "$LLM_OUTPUT"
    
    # Execute the command
    eval "$cmd" >> "$LLM_OUTPUT" 2>&1 || {
        echo "Error: Failed to execute goose command" >> "$LLM_OUTPUT"
        return 1
    }
}

# Using a conditional check for argc availability
if command -v argc >/dev/null 2>&1; then
    eval "$(argc --argc-eval "$0" "$@")" || {
        echo "Error: Failed to evaluate arguments with argc" >> "${LLM_OUTPUT:-/dev/stdout}"
        exit 1
    }
else
    # Fallback for when argc is not available
    # Setting default values
    argc_provider="openrouter"
    argc_model="deepseek/deepseek-chat-v3-0324"
    argc_with_builtin="developer"
    argc_text=""
    
    # Simple argument parser for direct execution without argc
    while [[ $# -gt 0 ]]; do
        case $1 in
            --provider=*)
                argc_provider="${1#*=}"
                shift
                ;;
            --model=*)
                argc_model="${1#*=}"
                shift
                ;;
            --with-builtin=*)
                argc_with_builtin="${1#*=}"
                shift
                ;;
            --text=*)
                argc_text="${1#*=}"
                shift
                ;;
            --text)
                shift
                if [[ $# -gt 0 ]]; then
                    argc_text="$1"
                    shift
                fi
                ;;
            *)
                echo "Warning: Unknown option $1" >> "${LLM_OUTPUT:-/dev/stdout}"
                shift
                ;;
        esac
    done
    
    # Set default output if not defined
    LLM_OUTPUT="${LLM_OUTPUT:-/dev/stdout}"
fi

# Execute main function
main
