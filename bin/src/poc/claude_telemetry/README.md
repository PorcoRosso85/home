# Claude Telemetry POC

claudeコマンドのインタラクティブモードを制御し、テレメトリデータを収集・分析するPOC。

## 機能

### Phase 1: プロセス制御
- claudeプロセスの起動・制御・終了
- 標準入出力の管理

### Phase 2: テレメトリ収集
- stream-json形式の出力をキャプチャ
- セッションIDとイベントの記録

### Phase 3: セッション管理
- SQLiteでセッション情報を永続化
- セッションIDによる再開機能

### Phase 4: 自動終了
- プロンプト実行後の自動終了
- /exitコマンドの自動送信

### Phase 5: クエリ分析
- ツール使用状況の分析
- Bashコマンドの抽出
- ファイル操作の分類

## 使用方法

```bash
# 基本的な使用
python main.py "What is 2 + 2?"

# 詳細レポート付き
python main.py "List files in current directory" --report

# セッション再開
python main.py "What did we discuss?" --resume <session-id>

# JSON出力
python main.py "Run ls command" --json --report

# 保存されたセッションのリスト
python main.py list
```

## アーキテクチャ

各モジュールは単一責任原則に従い、依存性注入により疎結合を実現：

- `claudeController.py`: プロセス制御
- `telemetryCapture.py`: データ収集
- `sessionManager.py`: セッション永続化
- `autoRunner.py`: 自動実行制御
- `queryAnalyzer.py`: クエリ分析
- `main.py`: 統合エントリーポイント

## テスト

各フェーズにテスト関数が含まれており、個別に実行可能：

```bash
python claudeController.py  # Phase 1
python telemetryCapture.py  # Phase 2
python sessionManager.py    # Phase 3
python autoRunner.py        # Phase 4
python queryAnalyzer.py     # Phase 5
```