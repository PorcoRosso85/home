#!/usr/bin/env bash
set -e

# @describe Set AI provider and model, then execute aichat with a prompt.
# @option --provider! The AI provider to use (e.g., "google", "openai", "anthropic").
# @option --model! The model to use (e.g., "gemini:gemini-2.0-flash", "gpt-4o").
# @option --prompt! The prompt to send to the AI model.

# @env LLM_OUTPUT=/dev/stdout The output path

ROOT_DIR="${LLM_ROOT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

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
    
    # Find the aichat executable - try multiple locations
    if command -v aichat > /dev/null 2>&1; then
        AICHAT_CMD=$(command -v aichat)
    elif [ -x "/usr/bin/aichat" ]; then
        AICHAT_CMD="/usr/bin/aichat"
    elif [ -x "/usr/local/bin/aichat" ]; then
        AICHAT_CMD="/usr/local/bin/aichat"
    elif [ -x "$HOME/.local/bin/aichat" ]; then
        AICHAT_CMD="$HOME/.local/bin/aichat"
    else
        echo "Error: aichat command not found in PATH or common locations" >> "$LLM_OUTPUT"
        return 1
    fi
    
    echo "Using aichat at: $AICHAT_CMD" >> "$LLM_OUTPUT"
    
    # Set provider and model
    export AICHAT_PROVIDER="$argc_provider"
    export AICHAT_MODEL="$argc_model"
    
    echo "Set AICHAT_PROVIDER=$AICHAT_PROVIDER" >> "$LLM_OUTPUT"
    echo "Set AICHAT_MODEL=$AICHAT_MODEL" >> "$LLM_OUTPUT"
    
    # Build and execute the command
    cmd="$AICHAT_CMD '$argc_prompt'"
    
    echo "Executing: $cmd" >> "$LLM_OUTPUT"
    
    # Execute the command
    eval "$cmd" >> "$LLM_OUTPUT" 2>&1 || {
        echo "Error: Failed to execute aichat command" >> "$LLM_OUTPUT"
        return 1
    }
}

eval "$(argc --argc-eval "$0" "$@")" || {
    echo "Error: Failed to evaluate arguments" >> "$LLM_OUTPUT"
    exit 1
}
