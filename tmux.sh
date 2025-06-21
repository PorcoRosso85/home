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
TMUX_APPS="${TMUX_APPS:-lazygit,yazi,hx}"
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

# アプリ数に応じてウィンドウを作成
for i in ${!APPS[@]}; do
    APP="${APPS[$i]}"
    
    if [ $i -gt 0 ]; then
        # 2つ目以降のアプリ用に新規ウィンドウ作成
        tmux new-window -t $SESSION_NAME -n "$APP"
    else
        # 最初のウィンドウ名を設定
        tmux rename-window -t $SESSION_NAME:0 "$APP"
    fi
    
    # アプリ別レイアウト設定
    if [ "$APP" = "lazygit" ]; then
        # lazygit: 2ペイン（左右分割）
        tmux split-window -h -t $SESSION_NAME:$i
        tmux resize-pane -t $SESSION_NAME:$i.0 -x 60%
        
        # 左ペイン（bash）
        tmux send-keys -t $SESSION_NAME:$i.0 "while true; do bash; sleep 1; done" Enter
        # 右ペイン（lazygit）
        tmux send-keys -t $SESSION_NAME:$i.1 "while true; do $APP; sleep 1; done" Enter
    else
        # その他のアプリ: 左2ペイン（上下）、中央2ペイン（上下）、右アプリ
        # まず左右3分割
        tmux split-window -h -t $SESSION_NAME:$i
        tmux split-window -h -t $SESSION_NAME:$i.0
        tmux resize-pane -t $SESSION_NAME:$i.0 -x ${LEFT_SIZE}%
        tmux resize-pane -t $SESSION_NAME:$i.1 -x ${LEFT_SIZE}%
        
        # 左ペインを上下分割
        tmux split-window -v -t $SESSION_NAME:$i.0 -p 50
        # 中央ペインを上下分割
        tmux split-window -v -t $SESSION_NAME:$i.2 -p 50
        
        # 各ペインでbash起動（左上、左下、中央上、中央下）
        tmux send-keys -t $SESSION_NAME:$i.0 "while true; do bash; sleep 1; done" Enter
        tmux send-keys -t $SESSION_NAME:$i.1 "while true; do bash; sleep 1; done" Enter
        tmux send-keys -t $SESSION_NAME:$i.2 "while true; do bash; sleep 1; done" Enter
        tmux send-keys -t $SESSION_NAME:$i.3 "while true; do bash; sleep 1; done" Enter
        
        # 右ペイン（アプリ）
        tmux send-keys -t $SESSION_NAME:$i.4 "while true; do $APP; sleep 1; done" Enter
    fi
done

# アプリ切り替えキーバインド（ウィンドウ切り替え）
for i in ${!APPS[@]}; do
    # Alt+数字キーでウィンドウ切り替え
    tmux bind-key -n M-$((i+1)) select-window -t $SESSION_NAME:$i
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

# ステータスラインにウィンドウ切り替え情報表示
STATUS="Switch: "
for i in ${!APPS[@]}; do
    STATUS="$STATUS Alt+$((i+1)):${APPS[$i]%%' '*}"
done
tmux set -g status-right "$STATUS"

# 最初のウィンドウを選択
tmux select-window -t $SESSION_NAME:0

# アタッチ
tmux attach-session -t $SESSION_NAME