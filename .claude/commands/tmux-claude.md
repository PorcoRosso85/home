# tmux-claude
/tmux-claude

# 説明
別のtmuxペインでClaudeに指示を送って返答を確認する

# 実行内容
1. 利用可能なペインを検索
2. Claudeまたはbashペインの一覧を表示
3. ユーザーに対象ペインを確認
4. 指示内容を送信して返答を確認

# 設定
```yaml
search:
  commands:
    - claude
    - bash
  exclude_current: true
  
send:
  key_sequence: C-m  # EnterではなくC-mを使用
  wait_time: 3      # 応答待機時間（秒）
  
capture:
  lines: 50         # 取得する行数
  method: tail      # 表示方法
```

# 実装手順
```yaml
steps:
  - name: "ペイン検索"
    command: |
      tmux list-panes -a -F "#{session_name}:#{window_index}.#{pane_index} #{pane_current_command} #{pane_title}"
    filter: "claude|bash"
    
  - name: "ペイン選択"
    prompt: "どのペインに送信しますか？"
    type: "selection"
    
  - name: "コマンド送信"
    command: |
      tmux send-keys -t {target} "{message}" && sleep 0.1 && tmux send-keys -t {target} C-m
      
  - name: "応答確認"
    command: |
      sleep {wait_time} && tmux capture-pane -t {target} -p | tail -{lines}
```

# 注意点
- Enterキーではなく`C-m`を使用すること
- メッセージ送信と`C-m`の間に0.1秒のsleepを入れること（確実な送信のため）
- Claudeの応答には少し時間がかかる
- 複数行の入力は`C-c`でキャンセルしてから再度送信