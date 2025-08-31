# tmux-based Multi-Agent Orchestration System Architecture

## システム概要

本システムは、tmuxをインフラストラクチャとして活用し、複数のAIエージェント（Claude Code, GPT等）を統合管理するオーケストレーションシステムである。libtmuxを使用することで、tmuxセッションへの手動アタッチを必要とせず、完全にプログラマブルな制御を実現する。

## アーキテクチャ構成

```
[Human (me)] 
    ↓
[Controller (0)] ← Python/libtmux
    ↓
[tmux Server]
    ├── [Session: agent-system]
    │   ├── [Window 0: Controller]
    │   ├── [Window 1: Worker-Claude-ProjectA]
    │   ├── [Window 2: Worker-GPT-ProjectB]
    │   └── [Window N: Worker-Agent-ProjectX]
    └── [State Management]
        ├── state.json (エージェント状態)
        └── logs/ (実行ログ)
```

## ファイル責務定義

### 1. `controller.py` - 中央制御コンポーネント

**責務:**
- すべてのワーカーエージェントのライフサイクル管理
- タスクの分配とスケジューリング
- ワーカー間の調整と結果の集約
- 障害検知と自己修復機能

**主要機能:**
- `spawn_worker(project_name, agent_type)`: 新規ワーカーの起動
- `send_task(worker_id, command)`: タスク送信
- `collect_results()`: 結果収集
- `health_check()`: ヘルスチェック（定期実行）
- `revive_worker(worker_id)`: ワーカー再起動

**状態管理:**
- ワーカーのpane_idマッピング
- タスクキューと実行状態
- エラーログとリトライカウント

### 2. `worker.py` - ワーカーエージェントコンポーネント

**責務:**
- 個別タスクの実行
- エージェント（Claude/GPT）との対話管理
- 終了マーカーによる同期プロトコル実装
- 実行結果のフォーマットと返却

**主要機能:**
- `initialize(agent_type, project_path)`: エージェント初期化
- `execute_task(command)`: タスク実行
- `emit_completion_marker(uuid)`: 終了マーカー出力
- `report_status()`: 状態報告

**プロトコル:**
```bash
# タスク実行
> command_to_execute
# 結果出力
... output ...
# 終了マーカー
---END-OF-OUTPUT-{UUID}---
```

### 3. `infrastructure.py` - tmuxインフラストラクチャ層

**責務:**
- libtmuxを使用したtmuxサーバーとの低レベル通信
- セッション、ウィンドウ、ペインの物理的管理
- コマンド送信と出力キャプチャの基本実装

**主要機能:**
- `connect_server()`: tmuxサーバー接続
- `create_session(name)`: セッション作成
- `create_pane(window_name)`: ペイン作成
- `send_keys(pane_id, command)`: キー送信
- `capture_output(pane_id)`: 出力取得
- `kill_pane(pane_id)`: ペイン削除

**エラーハンドリング:**
- tmuxサーバー接続失敗時の再接続
- ペインID不正時の例外処理
- タイムアウト管理

### 4. `application.py` - アプリケーション層

**責務:**
- ユースケースの実装
- ビジネスロジックの調整
- 高レベルAPIの提供

**主要機能:**
- `orchestrate_multi_project(projects)`: 複数プロジェクト並列処理
- `execute_workflow(workflow_definition)`: ワークフロー実行
- `generate_report()`: 実行レポート生成
- `backup_state()`: 状態バックアップ

**ユースケース例:**
```python
# 複数プロジェクトの並列テスト実行
async def run_parallel_tests(projects):
    workers = []
    for project in projects:
        worker = spawn_worker(project, 'claude')
        workers.append(worker)
    
    results = await gather_results(workers)
    return compile_test_report(results)
```

### 5. `domain.py` - ドメイン層

**責務:**
- ビジネスルールの定義
- エージェント管理ポリシー
- 状態遷移の制御

**主要機能:**
- `validate_worker_state(state)`: 状態検証
- `calculate_retry_policy(error_count)`: リトライポリシー計算
- `determine_agent_type(task_type)`: エージェント選択ロジック
- `enforce_resource_limits()`: リソース制限管理

**ドメインモデル:**
```python
class WorkerState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    DEAD = "dead"

class TaskPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
```

### 6. `variables.py` - 設定管理

**責務:**
- システム全体の設定値管理
- 環境別設定の切り替え
- 定数定義

**設定カテゴリ:**
```python
# tmux設定
TMUX_SESSION_NAME = "agent-system"
TMUX_SOCKET_PATH = "/tmp/tmux-agent"

# タイムアウト設定
COMMAND_TIMEOUT = 30  # seconds
HEALTH_CHECK_INTERVAL = 60  # seconds
WORKER_STARTUP_TIMEOUT = 10  # seconds

# 終了マーカー設定
END_MARKER_PREFIX = "---END-OF-OUTPUT-"
END_MARKER_SUFFIX = "---"

# 状態管理
STATE_FILE_PATH = "/var/lib/agent-system/state.json"
LOG_DIR = "/var/log/agent-system/"

# リトライポリシー
MAX_RETRY_COUNT = 3
RETRY_BACKOFF_FACTOR = 2
```

### 7. `cli.sh.example` - CLIインターフェース例

**責務:**
- システム操作のコマンドライン例提供
- デバッグ用コマンド集
- 運用スクリプトのテンプレート

**コマンド例:**
```bash
# システム起動
python controller.py start

# ワーカー追加
python controller.py add-worker --type claude --project /path/to/project

# ステータス確認
python controller.py status

# ヘルスチェック実行
python controller.py health-check

# デバッグ用tmuxアタッチ
tmux attach-session -t agent-system

# 特定ワーカーの出力確認
tmux capture-pane -t agent-system:1 -p
```

### 8. `README.md` - ドキュメント

**責務:**
- システム概要説明
- クイックスタートガイド
- 基本的な使用方法

**内容構成:**
- Installation
- Quick Start
- Basic Usage
- Architecture Overview
- Troubleshooting

## データフロー

### 1. タスク実行フロー

```
1. Controller がタスクを受信
2. 適切なWorkerを選択（または新規作成）
3. Infrastructure経由でコマンド送信
4. Worker がエージェントにタスク実行
5. 終了マーカーで完了検知
6. Controller が結果を収集・集約
```

### 2. ヘルスチェックフロー

```
1. Controller が定期的にhealth_check()実行
2. 各WorkerのPane存在確認
3. 応答性チェック（echoコマンド送信）
4. Dead Worker検出時、自動再起動
5. State更新
```

### 3. 状態永続化フロー

```
1. tmux-continuum による自動セッション保存
2. State.json への状態書き込み
3. 再起動時の自動復元
4. Pane IDの再マッピング
```

## セキュリティ考慮事項

1. **プロセス分離**: 各ワーカーは独立したペインで実行
2. **入力サニタイゼーション**: send_keysへの入力を検証
3. **リソース制限**: ワーカー数の上限設定
4. **ログ管理**: 機密情報のマスキング

## パフォーマンス最適化

1. **非同期処理**: asyncioによる並列タスク実行
2. **バッチ処理**: 複数コマンドの一括送信
3. **キャッシュ**: 頻繁に使用する出力のキャッシング
4. **遅延評価**: 必要時のみ出力キャプチャ

## 拡張ポイント

1. **エージェントタイプ追加**: WorkerクラスをPlugin形式で拡張
2. **カスタムプロトコル**: 終了マーカー以外の同期方式
3. **分散実行**: 複数マシンへのtmuxセッション分散
4. **Web UI**: Flask/FastAPIによるWeb管理画面