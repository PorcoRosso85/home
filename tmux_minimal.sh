#!/bin/bash

# 最小構成のtmuxスクリプト
SESSION_NAME="work"

# セッションが既に存在する場合は削除
tmux has-session -t $SESSION_NAME 2>/dev/null && tmux kill-session -t $SESSION_NAME

# 新しいセッションを作成（最初のウィンドウ名を指定）
tmux new-session -d -s $SESSION_NAME -n "editor"

# キーバインド設定
# Ctrl+Shift+矢印でペイン移動
tmux bind-key -n C-S-Left select-pane -L
tmux bind-key -n C-S-Right select-pane -R

# Alt+数字でウィンドウ切り替え
tmux bind-key -n M-1 select-window -t 1
tmux bind-key -n M-2 select-window -t 2
tmux bind-key -n M-3 select-window -t 3

# コントラスト設定
tmux set -g window-style 'fg=colour245'
tmux set -g window-active-style 'fg=colour255'

# ペイン保護設定
tmux set -g remain-on-exit on

# 最初のウィンドウを左右分割
tmux split-window -h -t $SESSION_NAME:editor

# 2つ目のウィンドウを作成（terminal）
tmux new-window -t $SESSION_NAME -n "terminal"
tmux split-window -h -t $SESSION_NAME:terminal

# 3つ目のウィンドウを作成（logs）
tmux new-window -t $SESSION_NAME -n "logs"
tmux split-window -h -t $SESSION_NAME:logs

# 各ペインで保護シェルを起動
for window in editor terminal logs; do
    for pane in 0 1; do
        tmux send-keys -t $SESSION_NAME:$window.$pane "trap '' INT TERM EXIT; set -o ignoreeof; IGNOREEOF=1000" Enter
        tmux send-keys -t $SESSION_NAME:$window.$pane "echo 'Protected pane - Use tmux kill-session to exit'" Enter
    done
done

# 最初のウィンドウに戻る
tmux select-window -t $SESSION_NAME:editor

# セッションにアタッチ
tmux attach-session -t $SESSION_NAME