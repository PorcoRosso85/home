#!/bin/bash

# tmuxセッション選択スクリプト

# tmuxセッションが存在しない場合
if ! tmux list-sessions &>/dev/null; then
    echo "No tmux sessions found. Creating new session..."
    exec bash $HOME/tmux.sh
fi

# セッション一覧を取得してfzfで選択
SESSION=$(tmux list-sessions -F "#{session_name}: #{session_windows} windows [#{session_attached} attached]" | \
    fzf --height=10 --layout=reverse --border --header="Select tmux session:" | \
    cut -d: -f1)

# 選択されたセッションにアタッチ
if [ -n "$SESSION" ]; then
    tmux attach-session -t "$SESSION"
else
    echo "No session selected."
fi