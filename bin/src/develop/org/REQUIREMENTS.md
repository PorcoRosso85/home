# Session Architecture 2機能分離 要件定義書

## 目的（What）
Session Architecture実装を以下の2つの機能に分離し、通信性能とスケーラビリティを最適化する：

### 機能1: 組織管理Session（Definer ↔ Designer通信）
- 同一session内でのDefiner-Designer間高速通信
- 組織全体の即時状態管理
- 管理オーバーヘッドの最小化

### 機能2: プロジェクト実行Session（Designer ↔ Developer通信）
- プロジェクト別独立session環境
- クロスsession通信によるタスク分離
- スケーラブルな並列プロジェクト実行

## 背景（Why）
Step 3A（Infrastructure層実装）により基盤が完成。現状の課題：

1. **組織管理の集約性不足**: Designer管理が分散し、即座の状態把握が困難
2. **プロジェクト分離の不完全性**: 同一session内でのプロジェクト実行は相互影響を与える
3. **スケーラビリティの制限**: 単一session管理では大規模並列処理に制約

## 期待成果

### 機能1: 組織管理Session最適化
- Session名: `org-definer-designers` 固定
- Designerの独立window化（pane → window変更）
- 同一session内高速通信（tmux内部パイプライン利用）
- リアルタイム状態統合管理

### 機能2: プロジェクト分離Session
- プロジェクト専用session生成: `dev-project-{name}`
- Cross-session通信による完全分離
- session lifecycle管理（作成・接続・廃棄）
- 並列プロジェクト実行のスケーラビリティ

### API互換性
- 既存の`start_designer`/`send_command_to_designer` API拡張
- `start_developer`/`send_command_to_developer_by_directory` session分離対応  
- `get_all_*_status` 統合状態管理継続

## 技術要求

### 機能1実装要求
```python
# Session統一管理
ORG_SESSION = "org-definer-designers"

# Designer window化
def start_designer_window(designer_id: str) -> Dict[str, Any]:
    # 独立window作成: "designer-{id}"
    pass

# 同一session内最適化通信
def send_to_designer_in_session(designer_id: str, message: str):
    # 高速な同一session内通信
    pass
```

### 機能2実装要求
```python  
# プロジェクト専用session
def generate_project_session_name(project_path: str) -> str:
    return f"dev-project-{Path(project_path).name}"

# Cross-session通信
def send_to_developer_session(project_path: str, message: str):
    # tmux send-keys -t session:window
    pass

# Session lifecycle
def ensure_project_session(project_path: str) -> str:
    # 存在確認・作成
    pass
```

## 検証要求
- 全48テスト（Step 3A）の互換性維持
- 新機能テストの追加
- 通信パフォーマンス測定（同一 vs 跨session）
- 並列プロジェクト実行のスケーラビリティ実証

## 完了条件
1. 機能1: 組織管理Session最適化の完全実装
2. 機能2: プロジェクト実行Session分離の完全実装  
3. 既存API互換性の維持（全テスト通過）
4. 新機能のテストカバレッジ追加
5. パフォーマンス向上の測定・実証

## リスク要因
- 既存APIの破壊的変更による互換性問題
- Cross-session通信の遅延・信頼性問題
- Session lifecycle管理の複雑性増大
- テスト環境でのsession管理の困難性

## 優先順位
1. **最重要**: 既存機能の互換性維持
2. **重要**: 機能1（組織管理Session）実装
3. **重要**: 機能2（プロジェクト分離Session）実装
4. **中程度**: パフォーマンス最適化
5. **低**: 将来拡張性の考慮