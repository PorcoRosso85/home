# /tmux
他のtmuxペインにタスクを送信

## 使用方法
```bash
/tmux <window.pane> <タスク>
```

## 形式要件
- **必須**: `window.pane`形式（例: 0.1, 1.2, 2.3）
- windowは整数、paneは整数
- ドット区切りの数値でない場合は処理を拒否

## 実行内容
0. 禁止事項確認: `bin/docs/conventions/prohibited_items.md`
1. **入力形式の検証**
   - `window.pane`形式（例: 0.1）であることを確認
   - 形式が正しくない場合は処理を中止
2. **送信先の確認**
   - `tmux list-panes -t <window> -F "#{window_index}.#{pane_index} #{pane_current_command}"` で確認
   - 指定されたwindow.paneが存在することを検証
3. **タスクを送信**
   - 指定されたwindow.paneにタスクを送信
   - 作業ディレクトリを自動設定
4. **送信後の動作確認**
   - 送信操作が期待通り動作したことを確認
   - エラー時は報告

## タスク送信フォーマット
```bash
# 1. 入力形式の検証（正規表現で確認）
if [[ ! "$1" =~ ^[0-9]+\.[0-9]+$ ]]; then
  echo "エラー: window.pane形式（例: 0.1）で指定してください"
  exit 1
fi

# 2. 指定されたウィンドウのペイン確認
tmux list-panes -t <window> -F "#{window_index}.#{pane_index} #{pane_current_command}"

# 3. タスク送信（window.pane形式で指定）
tmux send-keys -t <window.pane> "cd '$(pwd)' && [pane:<window.pane>] <タスク>" Enter

# 4. 送信確認
tmux capture-pane -t <window.pane> -p | tail -n 5
```

## 使用例
```bash
/tmux 0.1 "このファイルのテストを書いて"
/tmux 1.2 "コードレビューしてください"
/tmux 2.1 "ドキュメントを更新して"
```

## ペイン配置の前提
- あなたは通常 window x.0 にいる（例：0.0, 1.0, 2.0）
- x.1, x.2, x.3 は通常空いている
- ペイン指定がない場合は、現在 x.0 にいると仮定
- 空きペインは自分で確認してから使用可能

## ペイン選択ルール
1. **指定なしの場合**：
   - 現在 x.0 にいると仮定
   - x.1 から順に空きを確認して使用
   
2. **指定ありの場合**：
   - 指定されたペインより右側のペインを使用
   - 例：「ペイン1で」と指定 → 1以降（1, 2, 3）を使用