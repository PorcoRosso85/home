# JSONL Telemetry Monitor

JSONL形式のテレメトリーデータをリアルタイム監視。最小構成TDD実装。

## クイックスタート

```bash
# テスト（仕様確認）
python jsonl_monitor_minimal.py --test

# 使用
python jsonl_monitor_minimal.py your_file.jsonl
```

## 仕様（テストで定義）

```python
# ルール追加
monitor.add_rule(
    condition=lambda d: d.get("level") == "error",
    action=lambda d: print(f"🚨 {d['message']}")
)

# ファイル監視（新規行のみ）
monitor.tail_file("app.jsonl", skip_existing=True)
```

## 実装

- **jsonl_monitor_minimal.py** - 最小構成（218行、外部依存なし）
- **generate_test_jsonl.py** - テストデータ生成
- **pytest.ini** - pytest設定

## 動作例

```bash
# データ生成（別ターミナル）
python generate_test_jsonl.py test.jsonl

# 監視
python jsonl_monitor_minimal.py test.jsonl
```

出力：
```
🚨 ERROR: Connection timeout
🐌 SLOW: 1523ms
```