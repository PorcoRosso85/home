※必ず末尾まで100%理解したと断言できる状態になってから指示に従うこと
※このコマンドの説明はそれほど重要であるということを理解すること

# /tmux
他のtmuxペインにタスクを送信

## 使用方法
```bash
/tmux <window.pane> <タスク>  # 指定したwindow.paneに送信
```

## 実行内容
0. 禁止事項確認: `bin/docs/conventions/prohibited_items.md`
1. **引数チェック**
   - 引数が2つ未満の場合、使用方法を案内
   - 「/tmux <window.pane> <タスク>」の形式を要求
2. **window.pane形式の解析**
   - 引数を「window.pane」形式で解析（例: 1.2 → window 1, pane 2）
   - 不正な形式の場合はエラー
3. **送信先の存在確認**
   - 指定されたwindow.paneが存在するか確認
   - `tmux list-panes -t <window.pane>`で検証
4. **タスクを送信**
   - 指定されたwindow.paneにタスクを送信
   - 作業ディレクトリを自動設定
5. **送信後の状態確認**
   - 送信先paneの最新状態を取得
   - コマンドが正しく送信されたことを確認

## タスク送信フォーマット
```bash
# 1. 引数チェック
if [ $# -lt 2 ]; then
  echo "エラー: window.paneとタスクを指定してください"
  echo "使用方法: /tmux <window.pane> <タスク>"
  echo "例: /tmux 1.2 \"テストを実行して\""
  exit 1
fi

target="$1"
task="$2"

# 2. window.pane形式の検証
if ! [[ "$target" =~ ^[0-9]+\.[0-9]+$ ]]; then
  echo "エラー: window.pane形式で指定してください (例: 1.2)"
  exit 1
fi

# 3. 送信先の存在確認
if ! tmux list-panes -t "$target" &>/dev/null; then
  echo "エラー: $target は存在しません"
  echo "利用可能なpane:"
  tmux list-panes -a -F "  #{window_index}.#{pane_index}: #{pane_current_command}"
  exit 1
fi

# 4. 現在位置の取得（情報表示用）
current_location=$(tmux display-message -p '#{window_index}.#{pane_index}')
echo "現在位置: $current_location"
echo "送信先: $target"

# 5. タスク送信
echo "タスクを送信中..."
tmux send-keys -t "$target" "cd '$(pwd)' && $task" Enter

# 6. 送信後の状態確認
sleep 0.2  # コマンドが反映されるまで少し待つ

# 送信先の最新出力を表示（最後の5行）
echo "送信先の最新出力:"
tmux capture-pane -t "$target" -p | tail -n 5

# 送信確認メッセージ
echo "✓ タスクが正常に送信されました: $target"
```

## 使用例
```bash
# window.pane形式での送信
/tmux 1.2 "このファイルのテストを書いて"     # window 1, pane 2に送信
/tmux 2.0 "コードレビューしてください"       # window 2, pane 0に送信
/tmux 3.1 "ドキュメントを更新して"           # window 3, pane 1に送信

# 引数不足の場合
/tmux                                       # エラー: 使用方法を表示
/tmux 1.2                                   # エラー: タスクが必要
```

## 動作説明
- **window.pane形式**: `<window番号>.<pane番号>`形式で送信先を指定
- **絶対指定**: 現在位置に関係なく、任意のwindow.paneに送信可能
- **作業ディレクトリ保持**: 送信元の作業ディレクトリを送信先でも使用
- **存在確認**: 送信前に指定されたwindow.paneの存在を確認
- **結果表示**: 送信後の最新出力を表示して確認

## 前提条件
- tmuxセッション内で実行すること
- 送信先のwindow.paneが事前に作成されていること
- 送信先でClaude Codeなどが起動していること