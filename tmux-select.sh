#!/bin/bash

# tmuxセッション選択スクリプト

# 現在のセッションを記録（デタッチ前のセッション）
CURRENT_SESSION=$(tmux display-message -p '#S' 2>/dev/null)

# tmuxセッションが存在しない場合
if ! tmux list-sessions &>/dev/null; then
    echo "No tmux sessions found. Creating new session..."
    exec bash $HOME/tmux.sh
fi

# セッション一覧を取得してfzfで選択
SESSION=$(tmux list-sessions -F "#{session_name}: #{session_windows} windows [#{session_attached} attached]" | \
    fzf --height=10 --layout=reverse --border --header="Select tmux session: (ESC to cancel)" | \
    cut -d: -f1)

# 選択されたセッションにアタッチ、キャンセルの場合は元のセッションに戻る
if [ -n "$SESSION" ]; then
    tmux attach-session -t "$SESSION"
elif [ -n "$CURRENT_SESSION" ]; then
    # fzfをキャンセルした場合、元のセッションに戻る
    tmux attach-session -t "$CURRENT_SESSION"
else
    echo "No session selected."
fi