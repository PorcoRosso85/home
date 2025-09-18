# Claude Telemetry POC

## 責務

`claude --print --output-format stream-json`からJSONLを取得してクエリを抽出する

## 使用方法

```bash
python main.py "Your prompt here"
```

## 出力例

```
Executing: List files in current directory

Session ID: a9926c0b-2270-4a8c-9467-c2dcabbbbebd

=== QUERIES (1) ===

#1 Bash
  command: ls -la
  description: List files in current directory

=== OUTPUTS ===
I'll list the files in the current directory for you.
[RESULT] Listed files in current directory
```

## 抽出される情報

- セッションID
- 使用されたツール（tool_use）
- ツールの入力パラメータ
- アシスタントの出力テキスト