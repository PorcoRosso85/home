# /tmux
他のtmuxペインにタスクを送信

## 使用方法
```bash
/tmux <pane番号> <タスク>  # 現在のwindow内の指定paneに送信
```


## 実行内容
0. 禁止事項確認: `bin/docs/conventions/prohibited_items.md`
1. **引数チェック**
   - 引数が2つ未満の場合、ユーザーにpane番号の指定を要求
   - 「/tmux <pane番号> <タスク>」の形式を案内
2. **現在位置の取得**
   - `tmux display-message -p '#{window_index}.#{pane_index}'`で現在のwindow.paneを取得
   - 例: 3.0 → window 3のpane 0にいることを確認
3. **送信先の状態確認（送信前）**
   - 指定されたpane番号が現在のwindow内に存在するか確認
   - `tmux list-panes -t <window> -F "#{window_index}.#{pane_index} #{pane_current_command}"`
   - 送信先paneの現在のコマンド状態を取得・表示
   - 指定されたpaneが現在のpaneと同じ場合はエラー
4. **タスクを送信**
   - 指定されたwindow.paneにタスクを送信
   - 作業ディレクトリを自動設定
5. **送信後の状態確認（送信後）**
   - 送信先paneの最新状態を取得
   - コマンドが正しく送信されたことを確認
   - 送信先の最新出力を表示
   - エラー時は詳細を報告

## タスク送信フォーマット
```bash
# 1. 引数チェック
if [ $# -lt 2 ]; then
  echo "エラー: pane番号とタスクを指定してください"
  echo "使用方法: /tmux <pane番号> <タスク>"
  echo "例: /tmux 1 \"テストを実行して\""
  exit 1
fi

target_pane="$1"
task="$2"

# 2. 現在のwindow.paneを取得
current_location=$(tmux display-message -p '#{window_index}.#{pane_index}')
current_window=$(echo "$current_location" | cut -d. -f1)
current_pane=$(echo "$current_location" | cut -d. -f2)

echo "現在位置: window $current_window, pane $current_pane"

# 3. pane番号の検証
if ! [[ "$target_pane" =~ ^[0-9]+$ ]]; then
  echo "エラー: pane番号は数値で指定してください"
  exit 1
fi

if [ "$target_pane" = "$current_pane" ]; then
  echo "エラー: 現在いるpaneと同じpaneを指定しています"
  echo "別のpane番号を指定してください"
  exit 1
fi

# 4. 送信先paneの状態確認（送信前）
if ! tmux list-panes -t "$current_window.$target_pane" &>/dev/null; then
  echo "エラー: window $current_window に pane $target_pane は存在しません"
  echo "利用可能なpane:"
  tmux list-panes -t "$current_window" -F "  pane #{pane_index}: #{pane_current_command}"
  exit 1
fi

target="$current_window.$target_pane"

# 送信前の状態を取得
pre_command=$(tmux list-panes -t "$current_window" -F "#{pane_index} #{pane_current_command}" | grep "^$target_pane " | cut -d' ' -f2-)
echo "送信先: $target"
echo "送信前の状態: $pre_command"

# 5. タスク送信
echo "タスクを送信中..."
tmux send-keys -t "$target" "cd '$(pwd)' && [pane:$target] $task" Enter

# 6. 送信後の状態確認
sleep 0.2  # コマンドが反映されるまで少し待つ

# 送信後の状態を取得
post_command=$(tmux list-panes -t "$current_window" -F "#{pane_index} #{pane_current_command}" | grep "^$target_pane " | cut -d' ' -f2-)
echo "送信後の状態: $post_command"

# 送信先の最新出力を表示
echo "送信先の最新出力:"
tmux capture-pane -t "$target" -p | tail -n 10

# 送信確認メッセージ
echo "\n✓ タスクが正常に送信されました: $target"
```

## 使用例
```bash
# 現在window 3.0にいる場合
/tmux 1 "このファイルのテストを書いて"     # → 3.1に送信
/tmux 2 "コードレビューしてください"       # → 3.2に送信
/tmux 3 "ドキュメントを更新して"           # → 3.3に送信

# 引数不足の場合
/tmux                                   # エラー: pane番号の指定を要求
/tmux "タスク"                        # エラー: pane番号の指定を要求
```

## 動作説明
- **pane番号の明示的指定**: ユーザーが送信先paneを明示的に指定
- **現在位置の自動取得**: `tmux display-message -p`で現在のwindow.paneを完全に取得
- **送信前の状態確認**: 送信先paneの現在のコマンド状態を確認・表示
- **送信後の状態確認**: コマンド送信後の状態と最新出力を確認・表示
- **同一window内での動作**: 現在のwindowから移動せず、同じwindow内の指定paneを使用
- **引数不足時のアラート**: pane番号が指定されていない場合は使用方法を案内
- **エラーハンドリング**: 存在しないpaneや現在のpaneを指定した場合はエラー

## 前提条件
- 通常はwindow内のpane 0にいることを想定
- pane 1,2,3を並列タスク実行用に確保
- `tmux split-window -h`でpaneを事前に作成しておくことを推奨