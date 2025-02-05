THINK=openrouter/deepseek/deepseek-r1-distill-llama-70b:free
THINK=openrouter/deepseek/deepseek-r1-distill-llama-70b
CODE=$GEMINI_CODER

source $HOME/secret.sh
export LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib":$LD_LIBRARY_PATH
export LD_LIBRARY_PATH="/nix/store/v2ny69wp81ch6k4bxmp4lnhh77r0n4h1-zlib-1.3.1/lib":$LD_LIBRARY_PATH

edit_files=(
  ./.bash_profile
  ./.bashrc
  ./_.bashrc
  ./.profile
  ./_.profile
)

read_files=(
)



read_options=""
for file in "${read_files[@]}"; do
  read_options+="--read ${file} "
done

edit_options=""
for file in "${edit_files[@]}"; do
  edit_options+="--file ${file} "
done


architect() {
  uvx --from aider-chat aider \
    --no-auto-commits \
    ${read_options} ${edit_options} \
    --dark-mode \
    --model $GEMINI_THINKING \
    --editor-model $GEMINI_CODER \
    --architect
}

watcher() {
  uvx --from aider-chat aider \
    --no-auto-commits \
    ${read_options} ${edit_options} \
    --dark-mode \
    --model $THINK \
    --editor-model $CODE \
    --editor-edit-format diff \
    --watch-files --subtree-only 
}

message() {
  uvx --from aider-chat aider \
    --no-auto-commits \
    --model $GEMINI_THINKING \
    ${read_options} ${edit_options} \
    --message "$@"
}


main() {
  local OPTIND
  while getopts "awm:" opt; do  # `m` オプションに `:` を追加して引数を取る
    case "$opt" in
      a)
        architect
        exit 0
        ;;
      w)
        watcher
        exit 0
        ;;
      m)
        shift $((OPTIND-1))  # `-m` の後の引数を取得
        message "$@"  # 引数を `message` 関数に渡す
        exit 0
        ;;
      \?)
        echo "Usage: $(basename "$0") [-a|-w|-m message]" >&2
        exit 1
        ;;
    esac
  done

  # If no option is provided, show usage and exit
  if [[ -z "$opt" ]]; then
    echo "Usage: $(basename "$0") [-a|-w|-m message]" >&2
    exit 1
  fi
}
main "$@"
