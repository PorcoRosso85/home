#!/bin/bash
source $HOME/secret.sh

# 編集対象ファイルのリスト
edit_files=(
  ./.profile
)

read_files=(
  ./.bashrc
)

read_files() {
  for file in "${read_files[@]}"; do  # グローバル配列を直接参照
    echo "--- ${file} ---"
    if [ -f "$file" ]; then          # ファイル存在チェック追加
      cat "$file"
    else
      echo "Error: File not found: $file" >&2
    fi
  done
}

ai() {
  local prompt="$1"    # 第1引数をプロンプトとして取得
  shift                # 引数を1つシフトして残りをファイルリストに
  local read_files=("$@")

  AICHAT_PLATFORM=gemini \
  aichat \
  --prompt "あなたはソフトウェアのエキスパートであり英語で思考し日本語で回答する、特に指定がない限り以下のファイル群を参照します" \
  "$prompt" \
  <(
    for file in "${read_files[@]}"; do
      echo "--- ${file} ---"
      if [ -f "$file" ]; then
        cat "$file"
      else
        echo "Error: File not found: $file" >&2
      fi
    done
  )
}
