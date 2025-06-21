#!/bin/bash

# tmux統合スクリプト
# セッション名: ディレクトリ名-gitブランチ
GIT_BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
SESSION_NAME="$(basename $(pwd))-${GIT_BRANCH}"

# セッションが既に存在する場合は削除
tmux has-session -t $SESSION_NAME 2>/dev/null && tmux kill-session -t $SESSION_NAME

# 新しいセッションを作成
tmux new-session -d -s $SESSION_NAME -n "editor"

# キーバインド設定
# ペイン移動（プレフィックス経由）
tmux bind-key h select-pane -L
tmux bind-key j select-pane -D
tmux bind-key k select-pane -U
tmux bind-key l select-pane -R

# ウィンドウ切り替え（数字キーはデフォルトで動作）
# Ctrl-b + 1/2/3 でウィンドウ切り替え

# コントラスト設定
tmux set -g window-style 'fg=colour245'
tmux set -g window-active-style 'fg=colour255'

# ペイン保護設定
tmux set -g remain-on-exit on

# Vimモード設定
tmux set -g mode-keys vi
tmux set -g status-keys vi

# コピーモードのVimキーバインド
tmux bind-key -T copy-mode-vi v send-keys -X begin-selection
tmux bind-key -T copy-mode-vi y send-keys -X copy-selection-and-cancel
tmux bind-key -T copy-mode-vi V send-keys -X select-line
tmux bind-key -T copy-mode-vi C-v send-keys -X rectangle-toggle

# コピーモード（Ctrl-b + [ がデフォルト、追加で v も設定）
tmux bind-key v copy-mode

# セッション切り替え: デタッチしてtmux-select.shを使う
tmux bind-key S detach-client -E "bash $HOME/tmux-select.sh"

# 新規セッション作成: デタッチしてtmux-create.shを使う
tmux bind-key C detach-client -E "bash $HOME/tmux-create.sh"

# tmuxログ有効化（デバッグ用）
tmux set -g history-file ~/.tmux_history

# エディタウィンドウ設定（Helix）
tmux split-window -h -t $SESSION_NAME:editor
tmux send-keys -t $SESSION_NAME:editor.0 "
# 左ペインも保護
while true; do
    echo 'Left pane - Navigation'
    bash
    echo 'Shell exited. Restarting...'
    sleep 1
done" Enter
tmux send-keys -t $SESSION_NAME:editor.1 "
# Helixエディタを永続化
while true; do
    hx
    echo 'Helix closed. Restarting in 1 second...'
    sleep 1
done" Enter

# Gitウィンドウ設定（lazygit）
tmux new-window -t $SESSION_NAME -n "git"
tmux split-window -h -t $SESSION_NAME:git
tmux send-keys -t $SESSION_NAME:git.0 "
# 左ペインも保護
while true; do
    echo 'Left pane - Navigation'
    bash
    echo 'Shell exited. Restarting...'
    sleep 1
done" Enter
tmux send-keys -t $SESSION_NAME:git.1 "
# lazygitを永続化
while true; do
    lazygit
    echo 'Lazygit closed. Restarting in 1 second...'
    sleep 1
done" Enter

# ファイラーウィンドウ設定（yazi）
tmux new-window -t $SESSION_NAME -n "files"
tmux split-window -h -t $SESSION_NAME:files
tmux send-keys -t $SESSION_NAME:files.0 "
# 左ペインも保護
while true; do
    echo 'Left pane - Navigation'
    bash
    echo 'Shell exited. Restarting...'
    sleep 1
done" Enter
tmux send-keys -t $SESSION_NAME:files.1 "
# yaziを永続化
while true; do
    yazi
    echo 'Yazi closed. Restarting in 1 second...'
    sleep 1
done" Enter

# 最初のウィンドウに戻る
tmux select-window -t $SESSION_NAME:editor

# セッションにアタッチ
tmux attach-session -t $SESSION_NAME