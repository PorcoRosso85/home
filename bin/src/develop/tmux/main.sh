#!/bin/bash

# tmux統合スクリプト (main.sh)

# ヘルプ表示
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    cat << EOF
Usage: nix run flake#run [options]

tmux 水平2分割構成セッション作成スクリプト (Nix版)

環境変数:
  なし

実行例:
  # デフォルト設定で起動
  nix run flake#run


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

# セッション参加または作成
if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo "Attaching to existing session: $SESSION_NAME"
    tmux attach-session -t $SESSION_NAME
    exit 0
else
    echo "Creating new session: $SESSION_NAME"
    tmux new-session -d -s $SESSION_NAME
fi

# tmux設定
# ====================
# 共通関数定義
# ====================

# 2分割作成（50%-50%）
create_2_split() {
    local target="$1"
    tmux split-window -h -t "$target" -p 50
}

# 4分割作成（25%-25%-25%-25%）
create_4_split() {
    local target="$1"
    # 1回目: 50%-50%
    tmux split-window -h -t "$target" -p 50
    # 2回目: 左を50%-50%（全体の25%-25%）
    tmux split-window -h -t "$target.0" -p 50
    # 3回目: 右を50%-50%（全体の25%-25%）
    tmux split-window -h -t "$target.2" -p 50
}

# 欠けているペインを補充して指定数を維持
maintain_pane_count() {
    local target="$1"
    local expected_count="$2"
    local current_count="$3"
    
    if [ "$expected_count" -eq 2 ] && [ "$current_count" -eq 1 ]; then
        create_2_split "$target"
    elif [ "$expected_count" -eq 4 ] && [ "$current_count" -lt 4 ]; then
        case $current_count in
            1) create_4_split "$target" ;;
            2) # 2つある場合は、それぞれを分割
               tmux split-window -h -t "$target.0" -p 50
               tmux split-window -h -t "$target.2" -p 50 ;;
            3) # 3つある場合は、最初のペインを分割
               tmux split-window -h -t "$target.0" -p 50 ;;
        esac
    fi
}

# ====================
# tmux基本設定
# ====================
tmux set -g window-style 'fg=colour245'
tmux set -g window-active-style 'fg=colour255'
tmux set -g mode-keys vi
tmux set -g status-keys vi
tmux setw -g monitor-activity on
tmux set-option -g window-status-activity-style "bg=yellow,fg=black"

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
    
    if [ $idx -eq 0 ]; then
        # window 0は2分割
        create_2_split "$SESSION_NAME:$idx"
        # コマンド実行
        [ -n "$cmd1" ] && tmux send-keys -t "$SESSION_NAME:$idx.0" "$cmd1" Enter
        [ -n "$cmd2" ] && tmux send-keys -t "$SESSION_NAME:$idx.1" "$cmd2" Enter
    else
        # window 1以降は4分割
        create_4_split "$SESSION_NAME:$idx"
    fi
}

# hook内で使用する関数を環境変数として定義
export -f create_2_split
export -f create_4_split
export -f maintain_pane_count

# 共通hook設定関数
setup_hooks() {
    # ペイン数維持hook設定
    tmux set-hook -g pane-exited \
        "run-shell 'source ${BASH_SOURCE[0]}; \
        panes=\$(tmux list-panes -t #{session_name}:#{window_index} 2>/dev/null | wc -l); \
        idx=#{window_index}; \
        target=\"#{session_name}:#{window_index}\"; \
        if [ \$idx -eq 0 ]; then \
            maintain_pane_count \"\$target\" 2 \$panes; \
        else \
            maintain_pane_count \"\$target\" 4 \$panes; \
        fi'"
    
    # 新規window作成時の4分割設定
    tmux set-hook -t $SESSION_NAME after-new-window \
        "run-shell 'source ${BASH_SOURCE[0]}; \
        create_4_split \"#{session_name}:#{window_index}\"'"
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

# コピーモード
tmux bind-key -T copy-mode-vi v send-keys -X begin-selection
tmux bind-key -T copy-mode-vi y send-keys -X copy-selection-and-cancel
tmux bind-key -T copy-mode-vi V send-keys -X select-line
tmux bind-key -T copy-mode-vi C-v send-keys -X rectangle-toggle


# Window数2維持（windowが1つになったら自動で新規window作成）
tmux set-hook -g window-closed \
    "run-shell 'source ${BASH_SOURCE[0]}; \
    windows=\$(tmux list-windows -t #{session_name} 2>/dev/null | wc -l); \
    if [ \$windows -eq 1 ]; then \
        tmux new-window -t #{session_name} -c #{pane_current_path}; \
        sleep 0.1; \
        new_idx=\$(tmux list-windows -t #{session_name} -F "#{window_index}" | tail -1); \
        create_4_split \"#{session_name}:\$new_idx\"; \
    fi'"

# 最初のウィンドウを選択
tmux select-window -t "$SESSION_NAME:0"

# アタッチ
tmux attach-session -t $SESSION_NAME