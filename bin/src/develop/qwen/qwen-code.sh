#!/usr/bin/env bash

# OpenRouter configuration (can be overridden by environment variables)
: ${OPENAI_API_KEY:="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"}
: ${OPENAI_BASE_URL:="https://openrouter.ai/api/v1"}
: ${OPENAI_MODEL:="qwen/qwen3-coder"}

export OPENAI_API_KEY
export OPENAI_BASE_URL
export OPENAI_MODEL

# Run qwen-code from nixpkgs (binary name is 'qwen')
exec nix shell nixpkgs#qwen-code --command qwen "$@"