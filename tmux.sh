#!/bin/bash

# tmux統合スクリプト

# ヘルプ表示
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    cat << EOF
Usage: $0 [options]

tmux 3ペイン構成セッション作成スクリプト（1ウィンドウ版）

環境変数:
  TMUX_APPS         アプリリスト (デフォルト: "hx,lazygit,yazi")
  TMUX_RIGHT_SIZE   右ペインサイズ (デフォルト: 40)

実行例:
  # デフォルト設定で起動
  ./tmux.sh

  # カスタムアプリで起動
  TMUX_APPS="vim,tig,ranger" ./tmux.sh

  # 右ペインを50%に設定
  TMUX_RIGHT_SIZE=50 ./tmux.sh

  # 組み合わせ
  TMUX_APPS="hx,lazygit,btop" TMUX_RIGHT_SIZE=60 ./tmux.sh

キーバインド:
  Alt+1/2/3         右ペインのアプリ切り替え
  Ctrl-b + S        セッション切り替え
  Ctrl-b + C        新規セッション作成
  Ctrl-b + v        コピーモード
  Ctrl-b + h/j/k/l  ペイン移動
EOF
    exit 0
fi

# 環境変数でカスタマイズ可能（デフォルト値付き）
TMUX_APPS="${TMUX_APPS:-hx,lazygit,yazi}"
TMUX_RIGHT_SIZE="${TMUX_RIGHT_SIZE:-40}"  # 右ペインのサイズ（%）

# 配列に変換
IFS=',' read -ra APPS <<< "$TMUX_APPS"

# 左と中央のサイズを計算（残りを半分ずつ）
LEFT_SIZE=$(( (100 - TMUX_RIGHT_SIZE) / 2 ))

# セッション名
GIT_BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
SESSION_NAME="$(basename $(pwd))-${GIT_BRANCH}"

# セッション削除・作成
tmux has-session -t $SESSION_NAME 2>/dev/null && tmux kill-session -t $SESSION_NAME
tmux new-session -d -s $SESSION_NAME

# tmux設定
tmux set -g window-style 'fg=colour245'
tmux set -g window-active-style 'fg=colour255'
tmux set -g remain-on-exit on
tmux set -g mode-keys vi
tmux set -g status-keys vi

# 3ペイン作成
tmux split-window -h -t $SESSION_NAME
tmux split-window -h -t $SESSION_NAME.0
tmux resize-pane -t $SESSION_NAME.0 -x ${LEFT_SIZE}%
tmux resize-pane -t $SESSION_NAME.1 -x ${LEFT_SIZE}%

# 左・中央ペイン（共有シェル）
tmux send-keys -t $SESSION_NAME.0 "while true; do bash; sleep 1; done" Enter
tmux send-keys -t $SESSION_NAME.1 "while true; do bash; sleep 1; done" Enter

# 右ペイン（最初のアプリ）
tmux send-keys -t $SESSION_NAME.2 "while true; do ${APPS[0]}; sleep 1; done" Enter

# アプリ切り替えキーバインド（respawn-pane使用）
for i in ${!APPS[@]}; do
    APP="${APPS[$i]}"
    # Alt+数字キーでアプリ切り替え
    tmux bind-key -n M-$((i+1)) respawn-pane -t $SESSION_NAME.2 -k "while true; do $APP; sleep 1; done"
done

# キーバインド
tmux bind-key h select-pane -L
tmux bind-key j select-pane -D
tmux bind-key k select-pane -U
tmux bind-key l select-pane -R
tmux bind-key v copy-mode
tmux bind-key S detach-client -E "bash $HOME/tmux-select.sh"
tmux bind-key C detach-client -E "bash $HOME/tmux-create.sh"

# コピーモード
tmux bind-key -T copy-mode-vi v send-keys -X begin-selection
tmux bind-key -T copy-mode-vi y send-keys -X copy-selection-and-cancel
tmux bind-key -T copy-mode-vi V send-keys -X select-line
tmux bind-key -T copy-mode-vi C-v send-keys -X rectangle-toggle

# ステータスラインにアプリ情報表示
tmux set -g status-right "Apps: 1:${APPS[0]%%' '*} 2:${APPS[1]%%' '*} 3:${APPS[2]%%' '*}"

# アタッチ
tmux attach-session -t $SESSION_NAME