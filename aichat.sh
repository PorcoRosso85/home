AICHAT_PLATFORM=gemini MODEL=gemini:gemini-2.0-pro-exp-02-05
# AICHAT_PLATFORM=github MODEL=DeepSeek-R1
# AICHAT_PLATFORM=openrouter MODEL=deepseek/deepseek-r1
# AICHAT_PLATFORM=openrouter MODEL=openrouter:google/gemini-2.0-pro-exp-02-05:free
echo $AICHAT_PLATFORM, $MODEL
source $HOME/secret.sh

read_files=(
)
read_options=""
for file in "${read_files[@]}"; do
  read_options+="-f ${file} "
done


edit_files=(
  ./todo.sh
)
edit_options=""
for file in "${edit_files[@]}"; do
  edit_options+="-f ${file} "
done

prompts=(
  あなたはソフトウェアのエキスパートであり, 
  特に指定がない限り回答は端的に日本語で行うこと, 
)
prompt=""
for p in "${prompts[@]}"; do
  prompt+="${p}"
done

prompt="--prompt ${prompt}"

model_option="--model $MODEL"


chat() {
  # AICHAT_PLATFORM=$AICHAT_PLATFORM aichat \
  #   ${model_option} \
  #   ${prompt} \
  #   ${read_options} \
  #   ${edit_options} \
  #   "$@"
  local max_retries=3
  local retry_delay=2
  local exit_code
  local output

  for ((i=0; i<max_retries; i++)); do
    # aichatの実行結果を変数に取得
    output=$(AICHAT_PLATFORM=$AICHAT_PLATFORM aichat \
      ${model_option} \
      ${prompt} \
      ${read_options} \
      ${edit_options} \
      "$@" 2>&1)
    exit_code=$?

    # 出力が空でなく、かつ終了コードが0なら成功
    if [[ -n "$output" && $exit_code -eq 0 ]]; then
      echo "$output"
      return 0
    fi

    # 最終試行でなければ遅延
    if (( i < max_retries - 1 )); then
      sleep "$retry_delay"
    fi
  done

  # リトライ失敗
  echo "Error: No response after $max_retries attempts" >&2
  return $exit_code
}

rag() {
  AICHAT_PLATFORM=$AICHAT_PLATFORM aichat \
    ${model_option} \
    --rag "$1"
}

main() {
  local OPTIND
  local mode="chat"
  local rag_arg=""

  while getopts "zr:" opt; do
    case "$opt" in
      z)
        mode="chat"
        ;;
      r)
        mode="rag"
        rag_arg="$OPTARG"
        ;;
      \?)
        echo "Invalid option: -$OPTARG" >&2
        exit 1
        ;;
    esac
  done

  shift $((OPTIND-1))

  case "$mode" in
    "chat")
      chat "$@"  # 残りの引数をchat関数に渡す
      ;;
    "rag")
      rag "$rag_arg"
      ;;
  esac
}
main "$@"
