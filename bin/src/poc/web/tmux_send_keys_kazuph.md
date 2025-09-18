# tmux send-keys 使用方法 (kazuph記事より)

## 基本テンプレート
```bash
tmux send-keys -t %pane_number "command" && sleep 0.1 && tmux send-keys -t %pane_number Enter
```

## 並列タスク配分の例
```bash
tmux send-keys -t %27 "Task 1 content" && sleep 0.1 && tmux send-keys -t %27 Enter & \
tmux send-keys -t %28 "Task 2 content" && sleep 0.1 && tmux send-keys -t %28 Enter & \
tmux send-keys -t %25 "Task 3 content" && sleep 0.1 && tmux send-keys -t %25 Enter & \
wait
```

## ポイント
- `-t` でターゲットペインを指定
- `sleep 0.1` でコマンド実行を確実にする
- `&` で複数ペインのコマンドをチェイン
- `wait` で全コマンドの完了を待つ
- tmux環境での複数Claude Codeインスタンスへの効率的なタスク配分が可能

## 実際の送信方法確認
```bash
# 現在のセッション・ウィンドウ・ペインを確認
tmux list-panes -t nixos-dev:1 -F "Pane #{pane_index}: #{pane_title}"

# 特定のペインにコマンドを送る
tmux send-keys -t nixos-dev:1.1 "echo 'Hello from pane 1'" && sleep 0.1 && tmux send-keys -t nixos-dev:1.1 Enter
```