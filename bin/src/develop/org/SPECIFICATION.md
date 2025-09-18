# Session Architecture 2機能分離 技術設計書

## 1. アーキテクチャ設計

### 1.1 全体構成図

```
┌─────────────────────────────────────────────────────────────┐
│                  Session Architecture 2                        │
├─────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────┐                │
│  │    機能1: 組織管理Session                 │                │
│  │    [org-definer-designers]                │                │
│  │                                            │                │
│  │  ┌─────────┐  高速通信  ┌──────────┐   │                │
│  │  │ Definer │ ←─────────→ │Designer X│   │                │
│  │  │ (win 0) │             │ (win 1)  │   │                │
│  │  └─────────┘             └──────────┘   │                │
│  │       ↓                        ↓          │                │
│  │  ┌──────────┐           ┌──────────┐   │                │
│  │  │Designer Y│           │Designer Z│   │                │
│  │  │ (win 2)  │           │ (win 3)  │   │                │
│  │  └──────────┘           └──────────┘   │                │
│  └────────────────────┬───────────────────┘                │
│                        │ Cross-Session通信                     │
│  ┌────────────────────▼───────────────────┐                │
│  │    機能2: プロジェクト実行Sessions        │                │
│  │                                            │                │
│  │  ┌─────────────────────────────────┐   │                │
│  │  │ dev-project-email (Session)      │   │                │
│  │  │ └─ Developer (win 0)             │   │                │
│  │  └─────────────────────────────────┘   │                │
│  │  ┌─────────────────────────────────┐   │                │
│  │  │ dev-project-kuzu (Session)       │   │                │
│  │  │ └─ Developer (win 0)             │   │                │
│  │  └─────────────────────────────────┘   │                │
│  └──────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 通信フロー

#### 同一Session内通信（機能1）
```
Definer → Designer (同一session内)
- tmux send-keys -t org-definer-designers:1
- 最小遅延: <1ms
- 信頼性: 100%（同一プロセス）
```

#### Cross-Session通信（機能2）
```
Designer → Developer (別session)
- tmux send-keys -t dev-project-email:0
- 遅延: 1-5ms
- 信頼性: セッション存在確認必要
```

### 1.3 Session Lifecycle

```
[作成] → [アクティブ] → [アイドル] → [廃棄]
   ↑          ↓              ↑
   └──────────┴──────────────┘
      再利用パス
```

## 2. API仕様

### 2.1 機能1: 組織管理Session API

#### start_designer_window
```yaml
function: start_designer_window
parameters:
  designer_id: string  # "x", "y", "z"
returns:
  ok: boolean
  data:
    session_name: string  # "org-definer-designers"
    window_id: integer    # 1, 2, 3
    window_name: string   # "designer-x"
    status: string        # "active"
  error:
    message: string
    code: string
```

#### send_to_designer_optimized
```yaml
function: send_to_designer_optimized
parameters:
  designer_id: string
  message: string
  wait_for_response: boolean  # optional, default false
returns:
  ok: boolean
  data:
    sent_at: string  # ISO timestamp
    latency_ms: number
  error:
    message: string
```

### 2.2 機能2: プロジェクト実行Session API

#### ensure_project_session
```yaml
function: ensure_project_session
parameters:
  project_path: string
  reuse_existing: boolean  # default true
returns:
  ok: boolean
  data:
    session_name: string  # "dev-project-email"
    created: boolean
    reused: boolean
  error:
    message: string
```

#### send_to_project_session
```yaml
function: send_to_project_session
parameters:
  project_path: string
  message: string
  window_id: integer  # optional, default 0
returns:
  ok: boolean
  data:
    session_name: string
    sent_at: string
  error:
    message: string
```

#### cleanup_project_session
```yaml
function: cleanup_project_session
parameters:
  project_path: string
  force: boolean  # default false
returns:
  ok: boolean
  data:
    session_name: string
    cleaned: boolean
  error:
    message: string
```

### 2.3 既存API拡張

#### start_designer (拡張版)
```yaml
# 後方互換性維持しつつwindow化対応
function: start_designer
parameters:
  designer_id: string
  use_window: boolean  # optional, default true (新)
returns:
  # 既存と同じ構造 + window情報追加
```

#### start_developer (拡張版)
```yaml
# 別sessionでの起動対応
function: start_developer
parameters:
  project_directory: string
  use_separate_session: boolean  # optional, default true (新)
returns:
  # 既存と同じ構造 + session情報追加
```

## 3. データモデル

### 3.1 Session管理状態

```json
{
  "organization_session": {
    "name": "org-definer-designers",
    "created_at": "2025-09-06T10:00:00Z",
    "windows": {
      "0": {
        "name": "definer",
        "type": "definer",
        "active": true
      },
      "1": {
        "name": "designer-x",
        "type": "designer",
        "designer_id": "x",
        "active": true
      },
      "2": {
        "name": "designer-y",
        "type": "designer",
        "designer_id": "y",
        "active": false
      },
      "3": {
        "name": "designer-z",
        "type": "designer",
        "designer_id": "z",
        "active": true
      }
    }
  },
  "project_sessions": [
    {
      "name": "dev-project-email",
      "project_path": "/home/nixos/bin/src/poc/email",
      "created_at": "2025-09-06T10:05:00Z",
      "last_activity": "2025-09-06T10:15:00Z",
      "windows": {
        "0": {
          "name": "developer",
          "type": "developer",
          "active": true
        }
      }
    },
    {
      "name": "dev-project-kuzu",
      "project_path": "/home/nixos/bin/src/search/vss/kuzu",
      "created_at": "2025-09-06T10:10:00Z",
      "last_activity": "2025-09-06T10:20:00Z",
      "windows": {
        "0": {
          "name": "developer",
          "type": "developer",
          "active": true
        }
      }
    }
  ]
}
```

### 3.2 通信ログ構造

```yaml
communication_log:
  - timestamp: "2025-09-06T10:15:30.123Z"
    type: "intra_session"  # or "cross_session"
    from:
      session: "org-definer-designers"
      window: 0
      role: "definer"
    to:
      session: "org-definer-designers"
      window: 1
      role: "designer"
    message_size: 1024
    latency_ms: 0.5
    success: true
```

## 4. Developer向け実装ガイド

### 4.1 機能1: 組織管理Session実装

```python
# infrastructure.py への追加実装

class OrganizationSessionManager:
    ORG_SESSION_NAME = "org-definer-designers"
    
    def __init__(self):
        self.server = get_tmux_server()
        self.ensure_org_session()
    
    def ensure_org_session(self):
        """組織管理sessionの存在確認・作成"""
        if not self.server.has_session(self.ORG_SESSION_NAME):
            self.server.new_session(
                session_name=self.ORG_SESSION_NAME,
                window_name="definer",
                attach=False
            )
    
    def start_designer_window(self, designer_id: str) -> Dict[str, Any]:
        """Designer用windowの作成"""
        session = self.server.find_where({"session_name": self.ORG_SESSION_NAME})
        
        # Window名の生成
        window_name = f"designer-{designer_id}"
        
        # 既存window検索
        existing = session.find_where({"window_name": window_name})
        if existing:
            return {
                "ok": True,
                "data": {
                    "session_name": self.ORG_SESSION_NAME,
                    "window_id": existing.window_index,
                    "window_name": window_name,
                    "status": "reused"
                }
            }
        
        # 新規window作成
        window = session.new_window(
            window_name=window_name,
            attach=False
        )
        
        # Claude起動コマンド送信
        window.panes[0].send_keys(
            f"cd /home/nixos/bin/src/develop/org/designers/{designer_id} && claude",
            enter=True
        )
        
        return {
            "ok": True,
            "data": {
                "session_name": self.ORG_SESSION_NAME,
                "window_id": window.window_index,
                "window_name": window_name,
                "status": "active"
            }
        }
```

### 4.2 機能2: プロジェクト実行Session実装

```python
# infrastructure.py への追加実装

class ProjectSessionManager:
    
    def __init__(self):
        self.server = get_tmux_server()
        self.active_sessions = {}  # project_path -> session_name mapping
    
    def generate_session_name(self, project_path: str) -> str:
        """プロジェクトパスからsession名生成"""
        project_name = Path(project_path).name
        # 特殊文字をサニタイズ
        safe_name = re.sub(r'[^a-zA-Z0-9\-_]', '-', project_name)
        return f"dev-project-{safe_name}"
    
    def ensure_project_session(self, project_path: str, reuse: bool = True) -> Dict[str, Any]:
        """プロジェクトsessionの確保"""
        session_name = self.generate_session_name(project_path)
        
        # 既存session確認
        if reuse and self.server.has_session(session_name):
            self.active_sessions[project_path] = session_name
            return {
                "ok": True,
                "data": {
                    "session_name": session_name,
                    "created": False,
                    "reused": True
                }
            }
        
        # 新規session作成
        session = self.server.new_session(
            session_name=session_name,
            window_name="developer",
            start_directory=project_path,
            attach=False
        )
        
        # Developer起動
        session.windows[0].panes[0].send_keys("claude", enter=True)
        
        self.active_sessions[project_path] = session_name
        
        return {
            "ok": True,
            "data": {
                "session_name": session_name,
                "created": True,
                "reused": False
            }
        }
    
    def send_to_project_session(self, project_path: str, message: str) -> Dict[str, Any]:
        """Cross-session通信"""
        session_name = self.active_sessions.get(project_path)
        
        if not session_name or not self.server.has_session(session_name):
            # Session再作成
            self.ensure_project_session(project_path)
            session_name = self.active_sessions[project_path]
        
        # メッセージ送信
        target = f"{session_name}:0"
        self.server.cmd("send-keys", "-t", target, message, "Enter")
        
        return {
            "ok": True,
            "data": {
                "session_name": session_name,
                "sent_at": datetime.now().isoformat()
            }
        }
```

### 4.3 既存API互換性維持

```python
# application.py での互換性ラッパー

# 既存のstart_designer関数を拡張
def start_designer(designer_id: str, use_window: bool = True) -> Dict[str, Any]:
    """後方互換性を維持したDesigner起動"""
    if use_window:
        # 新実装: window化
        org_manager = OrganizationSessionManager()
        return org_manager.start_designer_window(designer_id)
    else:
        # 旧実装: pane分割（互換性のため残す）
        return legacy_start_designer_pane(designer_id)

# 既存のstart_developer関数を拡張
def start_developer(project_directory: str, use_separate_session: bool = True) -> Dict[str, Any]:
    """後方互換性を維持したDeveloper起動"""
    if use_separate_session:
        # 新実装: 別session
        project_manager = ProjectSessionManager()
        return project_manager.ensure_project_session(project_directory)
    else:
        # 旧実装: 同一session内window（互換性のため残す）
        return legacy_start_developer_window(project_directory)
```

## 5. テスト戦略

### 5.1 互換性テスト

```python
# test_backward_compatibility.py

def test_existing_api_compatibility():
    """既存48テストの継続通過確認"""
    # 旧モードでの動作確認
    result = start_designer("x", use_window=False)
    assert result["ok"]
    
    # 新モードでの動作確認
    result = start_designer("x", use_window=True)
    assert result["ok"]
    
    # API応答構造の互換性
    assert "session_name" in result["data"]
    assert "window_name" in result["data"]
```

### 5.2 パフォーマンステスト

```python
# test_performance.py

def test_intra_session_latency():
    """同一session内通信遅延測定"""
    start_time = time.perf_counter()
    send_to_designer_optimized("x", "test message")
    latency = (time.perf_counter() - start_time) * 1000
    assert latency < 1  # 1ms以内

def test_cross_session_latency():
    """Cross-session通信遅延測定"""
    start_time = time.perf_counter()
    send_to_project_session("/home/nixos/bin/src/poc/email", "test")
    latency = (time.perf_counter() - start_time) * 1000
    assert latency < 5  # 5ms以内
```

### 5.3 並列実行テスト

```python
# test_parallel_execution.py

def test_multiple_project_sessions():
    """複数プロジェクトの並列実行"""
    projects = [
        "/home/nixos/bin/src/poc/email",
        "/home/nixos/bin/src/search/vss/kuzu",
        "/home/nixos/bin/src/poc/container"
    ]
    
    sessions = []
    for project in projects:
        result = ensure_project_session(project)
        assert result["ok"]
        sessions.append(result["data"]["session_name"])
    
    # 全sessionが独立して存在
    assert len(set(sessions)) == len(projects)
    
    # 並列メッセージ送信
    for project in projects:
        result = send_to_project_session(project, f"test {project}")
        assert result["ok"]
```

### 5.4 Session Lifecycleテスト

```yaml
test_scenarios:
  - name: "session_creation"
    steps:
      - ensure_project_session("/path/to/project")
      - verify: session exists
  
  - name: "session_reuse"
    steps:
      - ensure_project_session("/path/to/project")
      - ensure_project_session("/path/to/project")  # 再度実行
      - verify: reused = true
  
  - name: "session_cleanup"
    steps:
      - cleanup_project_session("/path/to/project")
      - verify: session removed
```

## 6. 移行戦略

### Phase 1: 基盤実装（Day 1-2）
- OrganizationSessionManager実装
- ProjectSessionManager実装
- 基本テスト作成

### Phase 2: 既存API拡張（Day 3-4）
- start_designer/start_developer拡張
- 互換性ラッパー実装
- 既存48テスト通過確認

### Phase 3: 最適化（Day 5-6）
- 通信パフォーマンス最適化
- Session再利用ロジック
- エラーハンドリング強化

### Phase 4: 完全移行（Day 7）
- デフォルト動作を新実装に切り替え
- ドキュメント更新
- パフォーマンス測定レポート

## 7. リスク対応

### リスク1: 既存API破壊
- **対策**: 完全な後方互換性ラッパー実装
- **検証**: 全48テストの継続実行

### リスク2: Session管理の複雑化
- **対策**: 明確なLifecycle定義とログ記録
- **検証**: Session状態追跡システム

### リスク3: Cross-session通信障害
- **対策**: 自動再接続とリトライ機構
- **検証**: 障害注入テスト

## 8. 成功指標

| 指標 | 目標値 | 測定方法 |
|-----|--------|----------|
| 既存テスト通過率 | 100% (48/48) | pytest実行 |
| 同一session通信遅延 | <1ms | perf_counter測定 |
| Cross-session通信遅延 | <5ms | perf_counter測定 |
| 並列プロジェクト数 | 10+ | 同時session数 |
| API応答時間 | <100ms | 95パーセンタイル |