uv pip install -r requirements.txt
uv pip install -y \
    --no-cache-dir \
    --upgrade \
    functions-framework \
    google-cloud-aiplatform \
    google-cloud-bigquery \
    google-cloud-resource-manager \
    google-cloud-storage \
    anthropic \

pip install pytest anthropic functions-framework pydantic --upgrade google-cloud-aiplatform

pipx run aider-chat --no-git --dark-mode --no-auto-lint --model gemini/gemini-2.0-flash-exp --architect --editor-edit-format diff --editor-model openrouter/qwen/qwen-2.5-coder-32b-instruct
