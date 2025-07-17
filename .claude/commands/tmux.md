# /tmux
同一tmuxウィンドウ内の他のClaudeペインにタスクを送信

## 使用方法
```bash
/tmux <pane_id> <タスク>
```

## 実行内容
1. 指定されたペインIDにタスクを送信
2. 作業ディレクトリを自動設定
3. エラー時はメインペインに報告

## タスク送信フォーマット
```bash
tmux send-keys -t %<pane_id> "cd '$(pwd)' && [pane:<pane_id>] <タスク>" Enter
```

## 使用例
```bash
/tmux 1 "このファイルのテストを書いて"
/tmux 2 "コードレビューしてください"
```