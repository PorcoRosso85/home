# Requirement Graph Logic (RGL)

開発決定事項を管理し、関係性クエリを可能にするツール

## アーキテクチャ

規約準拠の3層構造:
- **domain/**: ビジネスロジック（外部依存なし）
- **application/**: ユースケース（domain層のみ依存）
- **infrastructure/**: 技術詳細（外部ライブラリ依存）

## 現在の実装

### Phase 1: JSONL実装（完了）
- 軽量な50次元埋め込み
- 類似性検索
- タグベース検索
- CLIインターフェース

### Phase 2: KuzuDB統合（準備中）
- query/: KuzuDBクエリ資産統合済み
- 関係性クエリ機能追加予定
- データ移行ツール作成予定

## 使用方法

### CLI
```bash
# 決定事項追加
PYTHONPATH=/home/nixos/bin/src python -m requirement.graph add "タイトル" "説明" --tags tag1 tag2

# 検索
PYTHONPATH=/home/nixos/bin/src python -m requirement.graph search "キーワード"

# 一覧
PYTHONPATH=/home/nixos/bin/src python -m requirement.graph list
```

### Python API
```python
from requirement.graph import create_rgl_service

service = create_rgl_service()
result = service["add_decision"](
    title="決定事項",
    description="詳細説明",
    tags=["tag1", "tag2"]
)
```

## 今後の計画

1. KuzuDBリポジトリ実装
2. 関係性クエリAPI追加
3. JSONL→KuzuDB移行ツール
4. 階層グラフ可視化