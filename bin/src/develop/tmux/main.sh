#!/bin/bash

# tmux統合スクリプト (main.sh)

# ヘルプ表示
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    cat << EOF
Usage: 
  ./tmux-shell.sh                          # 推奨: tmux-shell.sh経由で起動
  ./main.sh [options]                      # 直接実行（非推奨）
  nix develop -c bash main.sh [options]    # nix develop内で実行
  nix run .#tmux-session [options]         # flakeアプリとして実行

tmux 水平2分割構成セッション作成スクリプト (Nix版)

環境変数:
  なし

実行例:
  # 推奨: tmux-shell.sh経由で起動（bashrcも読み込まれる）
  ./tmux-shell.sh
  
  # 直接実行（実行権限が必要、非推奨）
  ./main.sh
  
  # nix develop環境内で実行
  nix develop -c bash main.sh
  
  # flakeアプリとして実行
  nix run .#tmux-session


キーバインド:
  Ctrl-b + 0/1      window切り替え
  Ctrl-b + S        セッション切り替え
  Ctrl-b + C        新規セッション作成
  Ctrl-b + v        コピーモード
  Ctrl-b + h/j/k/l  ペイン移動
  Ctrl-b + b        fzfでペインジャンプ
  Ctrl-b + c        flakeディレクトリ選択して新規window作成
EOF
    exit 0
fi


# セッション名（ディレクトリベース）
SESSION_NAME="$(basename $(pwd))"

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

# ====================
# tmux基本設定
# ====================
tmux set -g mode-keys vi
tmux set -g status-keys vi
tmux setw -g monitor-activity on

# ====================
# カラーテーマ設定（ミニマル暗め）
# ====================
# 基本カラー定義
BG_BASE="colour236"      # ベース背景（濃いグレー）
BG_ACTIVE="colour238"    # アクティブ背景（少し明るめ）
FG_DIM="colour242"       # 薄暗い文字
FG_NORMAL="colour245"    # 通常文字
FG_BRIGHT="colour250"    # 明るい文字
FG_ALERT="colour214"     # アラート（控えめなオレンジ）

# ペインスタイル
tmux set -g window-style "fg=$FG_NORMAL"
tmux set -g window-active-style "fg=colour255"

# ステータスバー
tmux set-option -g status-style "bg=$BG_BASE,fg=$FG_NORMAL"
tmux set-option -g window-status-current-style "bg=$BG_ACTIVE,fg=$FG_BRIGHT"
tmux set-option -g window-status-style "bg=$BG_BASE,fg=$FG_DIM"
tmux set-option -g window-status-activity-style "bg=$BG_BASE,fg=$FG_ALERT"
tmux set-option -g window-status-format " #I:#W "
tmux set-option -g window-status-current-format " #I:#W* "

# window名前を取得する関数
get_window_name() {
    local path="${1:-$PWD}"
    local rel_path="${path#/home/nixos/bin/}"
    
    # パスが長い場合は省略記法を使用
    if [ $(echo "$rel_path" | tr '/' '\n' | wc -l) -gt 3 ]; then
        # 最初のディレクトリと最後の2階層を保持
        local first=$(echo "$rel_path" | cut -d'/' -f1)
        local parent=$(basename $(dirname "$path"))
        local last=$(basename "$path")
        echo "$first/.../$parent/$last"
    else
        echo "$rel_path"
    fi
}

# window作成関数
create_window() {
    local idx=$1
    local name=$2
    local cmd1="${3:-}"
    local cmd2="${4:-}"
    
    if [ $idx -eq 0 ]; then
        # window 0の特別処理
        tmux rename-window -t "$SESSION_NAME:$idx" "$name"
        create_2_split "$SESSION_NAME:$idx"
        # コマンド実行
        [ -n "$cmd1" ] && tmux send-keys -t "$SESSION_NAME:$idx.0" "$cmd1" Enter
        [ -n "$cmd2" ] && tmux send-keys -t "$SESSION_NAME:$idx.1" "$cmd2" Enter
    else
        # window 1以降は単にnew-windowするだけ（hooksが4分割を処理）
        tmux new-window -t "$SESSION_NAME" -n "$name"
    fi
}

# hook設定
setup_hooks() {
    # ペイン終了時の処理
    tmux set-hook -g pane-exited \
        "run-shell 'idx=#{window_index}; \
        if [ \$idx -eq 0 ]; then \
            # window0は2分割維持
            panes=\$(tmux list-panes -t #{session_name}:0 2>/dev/null | wc -l); \
            [ \$panes -eq 1 ] && tmux split-window -h -t #{session_name}:0 -p 50; \
        elif [ \$idx -ne 0 ]; then \
            # window1以降は4分割維持（均等レイアウト使用）
            panes=\$(tmux list-panes -t #{session_name}:#{window_index} 2>/dev/null | wc -l); \
            if [ \$panes -lt 4 ] && [ \$panes -gt 0 ]; then \
                # 現在のwindowのディレクトリを取得
                cwd=\$(tmux display-message -t #{session_name}:#{window_index} -p \"#{pane_current_path}\"); \
                # 不足分のペインを追加（同じディレクトリで）
                while [ \$panes -lt 4 ]; do \
                    tmux split-window -h -t #{session_name}:#{window_index} -c \"\$cwd\"; \
                    panes=\$((panes + 1)); \
                done; \
                # 均等な水平レイアウトを適用（各ペイン25%）
                tmux select-layout -t #{session_name}:#{window_index} even-horizontal; \
            fi \
        fi'"
    
    # 新規window作成時は4分割（現在のディレクトリで）
    tmux set-hook -t $SESSION_NAME after-new-window \
        "run-shell 'cwd=\$(tmux display-message -t #{session_name}:#{window_index} -p \"#{pane_current_path}\"); \
        tmux split-window -h -t #{session_name}:#{window_index} -c \"\$cwd\" -p 50; \
        tmux split-window -h -t #{session_name}:#{window_index}.0 -c \"\$cwd\" -p 50; \
        tmux split-window -h -t #{session_name}:#{window_index}.2 -c \"\$cwd\" -p 50'"
}

setup_hooks

# Window作成（相対パス表示）
# window名前を取得
window_name=$(get_window_name "$PWD")
create_window 0 "$window_name" "lazygit" "yazi"
create_window 1 "$window_name"


# キーバインド
tmux bind-key h select-pane -L
tmux bind-key j select-pane -D
tmux bind-key k select-pane -U
tmux bind-key l select-pane -R
tmux bind-key v copy-mode

# fzfでペインジャンプ (prefix + b)
tmux bind-key b display-popup -E -w 80% -h 80% \
    "tmux list-panes -a -F '#{session_name}:#{window_index}.#{pane_index} #{window_name} [#{pane_current_command}]' | \
    fzf --reverse --header='Jump to pane (ESC to cancel):' \
        --preview 'tmux capture-pane -p -t {1} 2>/dev/null || echo \"Pane content not available\"' \
        --preview-window=right:50% | \
    cut -d' ' -f1 | xargs -I {} tmux switch-client -t {} \\; select-pane -t {}"

# flake.nixディレクトリ選択して新規window作成 (prefix + c)
# nix shell経由でfd + fzfを実行
tmux bind-key c display-popup -E -w 80% -h 80% \
    "nix shell nixpkgs#fd nixpkgs#fzf --command bash -c \"
        # get_window_name関数を定義
        get_window_name() {
            local path=\\\"\\\${1:-\\\$PWD}\\\"
            local rel_path=\\\"\\\${path#/home/nixos/bin/}\\\"
            
            if [ \\\$(echo \\\"\\\$rel_path\\\" | tr '/' '\\\\n' | wc -l) -gt 3 ]; then
                local first=\\\$(echo \\\"\\\$rel_path\\\" | cut -d'/' -f1)
                local parent=\\\$(basename \\\$(dirname \\\"\\\$path\\\"))
                local last=\\\$(basename \\\"\\\$path\\\")
                echo \\\"\\\$first/.../\\\$parent/\\\$last\\\"
            else
                echo \\\"\\\$rel_path\\\"
            fi
        }
        
        fd -H -t f 'flake.nix' '\$HOME' | \
        sed 's|/flake.nix\$||' | \
        fzf --reverse --header='Select flake directory:' | \
        while read selected_dir; do \
            window_name=\\\$(get_window_name \\\"\\\$selected_dir\\\"); \
            tmux new-window -n \\\"\\\$window_name\\\" -c \\\"\\\$selected_dir\\\"; \
        done\""


# コピーモード
tmux bind-key -T copy-mode-vi v send-keys -X begin-selection
tmux bind-key -T copy-mode-vi y send-keys -X copy-selection-and-cancel
tmux bind-key -T copy-mode-vi V send-keys -X select-line
tmux bind-key -T copy-mode-vi C-v send-keys -X rectangle-toggle



# 最初のウィンドウを選択
tmux select-window -t "$SESSION_NAME:0"

# アタッチ
tmux attach-session -t $SESSION_NAME