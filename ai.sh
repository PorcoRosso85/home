# AICHAT_PLATFORM=gemini MODEL=gemini:gemini-2.0-pro-exp-02-05
# AICHAT_PLATFORM=gemini MODEL=gemini:gemini-2.0-flash-thinking-exp-01-21
# Unavailable
# AICHAT_PLATFORM=openrouter MODEL=openai/gpt-4o-mini
# AICHAT_PLATFORM=openrouter MODEL=deepseek/deepseek-chat
# AICHAT_PLATFORM=openrouter MODEL=google/gemini-2.0-flash-001
# AICHAT_PLATFORM=openrouter MODEL=google/gemini-2.0-flash-thinking-exp:free
AICHAT_PLATFORM=openrouter MODEL=openrouter:google/gemini-2.0-pro-exp-02-05:free
# AICHAT_PLATFORM=openrouter MODEL=openrouter:deepseek/deepseek-r1:free
# AICHAT_PLATFORM=openrouter MODEL=openrouter:openai/o3-mini-high
# AICHAT_PLATFORM=openrouter MODEL=openrouter/deepseek/deepseek-r1:free
# AICHAT_PLATFORM=github MODEL=deepSeek-r1

# THINK=openrouter/perplexity/r1-1776
# THINK=gemini/gemini-2.0-pro-exp-02-05
# THINK=gemini/gemini-2.0-flash-thinking-exp-01-21
THINK=openrouter/google/gemini-2.0-flash-thinking-exp-01-21:free
# THINK=openrouter/google/gemini-2.0-pro-exp-02-05:free
# THINK=openrouter/openai/o3-mini-high
# CODE=openrouter/google/gemini-2.0-flash-001
# CODE=openrouter/google/gemini-2.0-pro-exp-02-05:free
CODE=gemini/gemini-2.0-pro-exp-02-05
# CODE=openrouter/openai/gpt-4o-mini

read_files=(
./tested.log
)
edit_files=(
# ./req.sh
# ./main.py
./src/function/main.py
)
user_prompts=(
以下端的に回答してほしい
なぜエラー？
)
user_prompt=""
for p in "${user_prompts[@]}"; do
  user_prompt+="$p"
done

system_prompts=(
あなたはソフトウェアのエキスパートであり, 
特に指定がない限り回答は端的に日本語で行うこと, 
)

source ../.config/aichat/main.sh
source ../.config/aider/main.sh

test_log_file_path="./tested.log"

main() {
  local OPTIND
  local mode=""

  while getopts "acmrwx" opt; do
    case "$opt" in
      # aichat
      c)
        shift
        chat "$user_prompt" "$@"
        exit "$?"
        ;;
      x)
        shift
        chat "$user_prompt" "$@"
        echo TESTED 
        source ./test.sh
        echo "testing... : ${edit_files[0]}"
        test_main "${edit_files[0]}" $test_log_file_path

        git diff --cached --quiet || git commit -m "auto"
        git add "${edit_files[0]}"
        git diff --cached --quiet || git commit -m "auto"
        exit "$?"
        ;;
      r)
        shift
        rag "$@"
        exit 0
        ;;

      # aider
      m)
        shift
        local combined_args="$user_prompt "
        for arg in "$@"; do
          combined_args+="$arg "
        done
        message "$combined_args"
        exit 0
        ;;
      a)
        architect
        exit 0
        ;;
      w)
        watcher
        exit 0
        ;;
      *)
        repl
        exit 0
        # uvx llm
        # npx @builder.io/micro-agent
        ;;
      \?)
        echo "Usage: $(basename "$0") [-a -c -r -w message]" >&2
        echo "Invalid option: -$OPTARG" >&2
        exit 1
        ;;
    esac
  done

  shift $((OPTIND-1))
}
main "$@"
