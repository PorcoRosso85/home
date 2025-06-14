# AICHAT_PLATFORM=gemini MODEL=gemini:gemini-2.0-pro-exp-02-05
# AICHAT_PLATFORM=gemini MODEL=gemini:gemini-2.0-flash-thinking-exp-01-21
# AICHAT_PLATFORM=github MODEL=deepSeek-r1
AICHAT_PLATFORM=openrouter MODEL=openrouter:google/gemini-2.0-pro-exp-02-05:free
# AICHAT_PLATFORM=openrouter MODEL=openrouter:google/gemini-2.0-flash-thinking-exp:free
# AICHAT_PLATFORM=openrouter MODEL=openrouter:google/gemini-2.0-flash-lite-preview-02-05:free
# AICHAT_PLATFORM=openrouter MODEL=openrouter:deepseek/deepseek-r1:free
# AICHAT_PLATFORM=openrouter MODEL=openrouter:openai/o3-mini-high
# AICHAT_PLATFORM=deepseek MODEL=deepseek:deepseek-chat
# AICHAT_PLATFORM=deepseek MODEL=deepseek:deepseek-reasoner

# THINK=openrouter/perplexity/r1-1776
# THINK=openrouter/google/gemini-2.0-pro-exp-02-05:free
# THINK=openrouter/google/gemini-2.0-flash-thinking-exp-01-21:free
# THINK=gemini/gemini-2.0-pro-exp-02-05
THINK=gemini/gemini-2.0-flash-thinking-exp-01-21
# THINK=openrouter/openai/o3-mini-high
# THINK=anthropic/claude-3.7-sonnet:thinking
# THINK=deepseek/deepseek-reasoner
# THINK=deepseek/deepseek-chat
CODE=deepseek/deepseek-coder
# CODE=openrouter/google/gemini-2.0-flash-001
# CODE=openrouter/google/gemini-2.0-pro-exp-02-05:free
# CODE=gemini/gemini-2.0-pro-exp-02-05
# CODE=openrouter/openai/gpt-4o-mini

oh() {
  prompt=$1
  shift
  source ../secret.sh
  WORKSPACE_BASE=$(pwd)
  LLM_MODEL=openrouter/google/gemini-2.0-flash-001
  LLM_API_KEY=$OPENROUTER_API_KEY
  docker run -it \
    --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.27-nikolaik \
    -e SANDBOX_USER_ID=$(id -u) \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -e LLM_API_KEY=$LLM_API_KEY \
    -e LLM_MODEL=$LLM_MODEL \
    -e LOG_ALL_EVENTS=true \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.openhands-state:/.openhands-state \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app-$(date +%Y%m%d%H%M%S) \
    docker.all-hands.dev/all-hands-ai/openhands:0.27 \
    python -m openhands.core.main -t "$prompt"
}

oh "$@"
