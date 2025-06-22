#!/bin/bash

# tmux統合スクリプト

# ヘルプ表示
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    cat << EOF
Usage: $0 [options]

tmux 水平2分割構成セッション作成スクリプト

環境変数:
  なし

実行例:
  # デフォルト設定で起動
  ./tmux.sh


キーバインド:
  Ctrl-b + 0/1      window切り替え
  Ctrl-b + S        セッション切り替え
  Ctrl-b + C        新規セッション作成
  Ctrl-b + v        コピーモード
  Ctrl-b + h/j/k/l  ペイン移動
EOF
    exit 0
fi


# セッション名
GIT_BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
SESSION_NAME="$(basename $(pwd))-${GIT_BRANCH}"

# セッション削除・作成
tmux has-session -t $SESSION_NAME 2>/dev/null && tmux kill-session -t $SESSION_NAME
tmux new-session -d -s $SESSION_NAME

# tmux設定
tmux set -g window-style 'fg=colour245'
tmux set -g window-active-style 'fg=colour255'
tmux set -g mode-keys vi
tmux set -g status-keys vi

# window作成関数
create_window() {
    local idx=$1
    local name=$2
    local cmd1="${3:-}"
    local cmd2="${4:-}"
    
    if [ $idx -eq 0 ]; then
        tmux rename-window -t "$SESSION_NAME:$idx" "$name"
    else
        tmux new-window -t "$SESSION_NAME" -n "$name"
    fi
    
    # 水平2分割
    tmux split-window -h -t "$SESSION_NAME:$idx"
    
    # コマンド実行
    [ -n "$cmd1" ] && tmux send-keys -t "$SESSION_NAME:$idx.0" "$cmd1" Enter
    [ -n "$cmd2" ] && tmux send-keys -t "$SESSION_NAME:$idx.1" "$cmd2" Enter
}

# 共通hook設定関数
setup_hooks() {
    # 2分割維持hook設定
    tmux set-hook -g pane-exited \
        "run-shell 'panes=\$(tmux list-panes -t #{session_name}:#{window_index} 2>/dev/null | wc -l); \
        if [ \$panes -eq 1 ]; then \
            tmux split-window -h -t #{session_name}:#{window_index}; \
        fi'"
    
    # 新規window作成時の2分割設定
    tmux set-hook -t $SESSION_NAME after-new-window \
        "run-shell 'tmux split-window -h -t #{session_name}:#{window_index}'"
}

setup_hooks

# Window作成
create_window 0 "apps" "lazygit" "yazi"
create_window 1 "bash"


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


# Window数2維持（windowが1つになったら自動で新規window作成）
tmux set-hook -g window-closed \
    "run-shell 'windows=\$(tmux list-windows -t #{session_name} 2>/dev/null | wc -l); \
    if [ \$windows -eq 1 ]; then \
        tmux new-window -t #{session_name} -c #{pane_current_path}; \
        sleep 0.1; \
        new_idx=\$(tmux list-windows -t #{session_name} -F "#{window_index}" | tail -1); \
        tmux split-window -h -t #{session_name}:\$new_idx; \
    fi'"

# 最初のウィンドウを選択
tmux select-window -t "$SESSION_NAME:0"

# アタッチ
tmux attach-session -t $SESSION_NAME