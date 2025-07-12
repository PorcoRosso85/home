# requirement/template 移行タスク詳細

## 概要
requirement/graphからrequirement/templateへの移行計画。
後方互換性を完全に削除し、テンプレートベースの要件管理システムを構築する。

## 重要な設計決定

### 最終的なディレクトリ構造
```
requirement/template/
├── domain/                    # ドメインモデル・ルール
│   ├── requirement.py         # 要件エンティティ定義
│   ├── duplicate_rule.py      # 重複判定ルール  
│   ├── template_spec.py       # テンプレート仕様
│   └── ddl/                  # ドメインモデルの構造定義（requirement/graphから完全コピー）
│       ├── README.md
│       └── migrations/
├── application/              # ユースケース
│   ├── create_requirement_use_case.py
│   ├── check_duplicate_use_case.py  
│   └── query/               # ユースケースのクエリテンプレート（requirement/graphから完全コピー）
│       ├── dml/
│       └── dql/
└── infrastructure/           # 技術的詳細のみ
    ├── kuzu/
    │   ├── connection.py     # DB接続
    │   ├── index_manager.py  # VSS/FTSインデックス管理
    │   └── query_executor.py # クエリ実行
    ├── template_loader.py    # ファイルシステムアクセス
    ├── vss_adapter.py       # POC search統合
    └── variables/           # 環境変数読み込み（requirement/graphから移植）
        └── env.py
```

### アーキテクチャ決定事項
1. **テンプレートベース入力**
   - 生のCypherクエリは受け付けない
   - すべての操作はテンプレート経由
   - パラメータ化により安全性を確保

2. **VSS/FTS統合方針**  
   - 要件作成時に自動的に重複チェック
   - 類似要件を情報として表示（警告ではない）
   - 作成は常に可能（ユーザーが判断）

3. **バージョニング**
   - テンプレート内で自動処理
   - 専用APIは提供しない
   - Gitのようなappend-onlyモデル

## 現在の状況

### 完了したタスク
- POC searchモジュールのVSS+FTS統合の意義を確認
- requirement/templateの最小機能セット定義
- DDD準拠ディレクトリ構造の設計
- DDL/DML/DQLの配置場所決定（DDL→domain層、DML/DQL→application層）
- テンプレートベース入力方式の決定
- semantic_searchパスの扱い決定（内部ユーティリティ化）

### 発見された課題
1. **DDLにembeddingフィールドがない**
   - RequirementEntityテーブルにembedding DOUBLE[384]の追加が必要
   
2. **POC searchの前提条件**
   - embedding生成メカニズムの実装
   - KuzuDB拡張機能（vector/fts）のインストール手順
   - インデックス作成・管理の実装

## Phase 1: POC search統合準備（前提条件）

### 1.1 embedding生成の実装
```python
# requirement/template/infrastructure/embedding_generator.py
def generate_embedding(text: str) -> List[float]:
    """
    テキストから384次元のembeddingを生成
    初期実装：ハッシュベースのモックembedding
    将来実装：実際の埋め込みモデル（PLaMo等）
    """
    pass
```

### 1.2 KuzuDB拡張機能インストール手順書
```bash
# requirement/template/docs/SETUP.md
1. KuzuDB接続確立
2. INSTALL EXTENSION vector;
3. INSTALL EXTENSION fts;
4. 動作確認クエリ実行
```

### 1.3 インデックス管理実装
```python
# requirement/template/infrastructure/kuzu/index_manager.py
class IndexManager:
    def create_vss_index(self, connection):
        """CREATE_VECTOR_INDEX実行"""
        
    def create_fts_index(self, connection):
        """CREATE_FTS_INDEX実行"""
        
    def ensure_indexes_exist(self, connection):
        """インデックスの存在確認と作成"""
```

## Phase 2: 基盤構築

### 2.1 ディレクトリ構造作成
```bash
mkdir -p /home/nixos/bin/src/requirement/template/{domain,application,infrastructure}
mkdir -p /home/nixos/bin/src/requirement/template/domain/ddl/migrations
mkdir -p /home/nixos/bin/src/requirement/template/application/query/{dml,dql}
mkdir -p /home/nixos/bin/src/requirement/template/infrastructure/{kuzu,variables}
```

### 2.2 DDL移植と修正
```bash
# DDLコピー
cp -r /home/nixos/bin/src/requirement/graph/ddl/* /home/nixos/bin/src/requirement/template/domain/ddl/

# 新規マイグレーションファイル作成
# requirement/template/domain/ddl/migrations/3.3.0_add_embedding.cypher
ALTER TABLE RequirementEntity ADD COLUMN embedding DOUBLE[384];
```

### 2.3 DML/DQL移植
```bash
cp -r /home/nixos/bin/src/requirement/graph/query/* /home/nixos/bin/src/requirement/template/application/query/
```

### 2.4 環境変数管理移植
```bash
cp -r /home/nixos/bin/src/requirement/graph/infrastructure/variables/* /home/nixos/bin/src/requirement/template/infrastructure/variables/
```

## Phase 3: テスト移行

### 3.1 全テストファイル複製
```bash
# ルートレベルテスト
cp /home/nixos/bin/src/requirement/graph/test_*.py /home/nixos/bin/src/requirement/template/

# 各層のテスト
cp -r /home/nixos/bin/src/requirement/graph/domain/test_*.py /home/nixos/bin/src/requirement/template/domain/
cp -r /home/nixos/bin/src/requirement/graph/infrastructure/test_*.py /home/nixos/bin/src/requirement/template/infrastructure/
```

### 3.2 削除対象テスト（以下のファイルを削除）
```
# バージョニングAPI関連
test_version_*.py
test_versioning_*.py

# Cypher直接実行関連
test_cypher_templates.py
test_query_validator.py
test_cypher_executor.py

# 複雑なビジネスルール
test_inconsistency_detection.py
test_requirement_conflicts.py
test_constraints.py

# 旧アーキテクチャ固有
test_executive_engineer_*.py
test_embedder.py  # 50次元エンベッダー
```

### 3.3 テスト修正必要箇所
- import文：`requirement.graph` → `requirement.template`
- 入力形式：Cypher文字列 → template/parameters形式
- embedding次元数：50 → 384

## Phase 4: コア実装

### 4.1 main.py実装
```python
# requirement/template/main.py
def main():
    """
    入力形式:
    {
        "type": "template",
        "template": "create_versioned_requirement",
        "parameters": {...}
    }
    """
    # 1. 入力パース
    # 2. パラメータからtitle/description抽出
    # 3. embedding生成
    # 4. 重複チェック（hybrid_search呼び出し）
    # 5. テンプレート実行
    # 6. 結果返却
```

### 4.2 テンプレートローダー実装
```python
# requirement/template/infrastructure/template_loader.py
class TemplateLoader:
    def load_template(self, template_name: str) -> str:
        """application/query/dml/からテンプレート読み込み"""
```

### 4.3 POC search統合
```python
# requirement/template/infrastructure/vss_adapter.py
from poc.search.hybrid.requirement_search_engine import hybrid_search

class VSSAdapter:
    def check_duplicates(self, connection, text: str) -> List[Dict]:
        """POC searchを使用して重複チェック"""
        results = hybrid_search(connection, text, k=5)
        return results
```

## Phase 5: 統合とテスト

### 5.1 E2Eテストシナリオ
```python
# requirement/template/test_e2e_scenarios.py
def test_新規要件作成_重複なし():
    """重複がない場合の正常系"""
    
def test_新規要件作成_重複あり():
    """類似要件が存在する場合"""
    
def test_embedding生成エラー():
    """embedding生成に失敗した場合"""
```

### 5.2 パフォーマンステスト
- embedding生成時間測定
- VSS/FTS検索時間測定
- 全体のレスポンスタイム測定

### 5.3 本番環境準備
- KuzuDB拡張機能インストール確認
- 既存データのembedding生成（バックフィル）
- インデックス作成

## 実装優先順位

1. **必須（MVP）**
   - ディレクトリ構造作成
   - DDL/DML/DQL移植
   - main.py基本実装
   - モックembedding実装

2. **重要**
   - POC search統合
   - FTSによる重複チェック
   - テスト移行

3. **将来対応**
   - 実際の埋め込みモデル統合
   - VSSによる高度な類似検索
   - パフォーマンス最適化

## 見積もり工数

- Phase 1（前提条件）: 2-3日
- Phase 2（基盤構築）: 1-2日
- Phase 3（テスト移行）: 2-3日
- Phase 4（コア実装）: 3-4日
- Phase 5（統合テスト）: 1-2日

**合計**: 9-14日（約2週間）

## リスクと対策

1. **KuzuDB拡張機能の可用性**
   - リスク：vector/fts拡張が利用できない環境
   - 対策：フォールバック実装（通常のCONTAINS検索）

2. **embedding生成のパフォーマンス**
   - リスク：リアルタイムembedding生成が遅い
   - 対策：非同期処理、キャッシュ、バッチ処理

3. **既存データの移行**
   - リスク：大量の既存要件のembedding生成
   - 対策：段階的バックフィル、優先度付け

## 成功の定義

1. テンプレートベースで要件を作成できる
2. 重複要件を自動検出できる（FTSベースでもOK）
3. 既存のDDL/DML/DQLが動作する
4. テストカバレッジ80%以上
5. レスポンスタイム1秒以内

## 次のアクション

1. このタスクリストのレビューと承認
2. Phase 1の前提条件確認
3. ディレクトリ構造作成から開始

## 議論の履歴と決定事項

### テンプレート入力形式
```json
{
  "type": "template",
  "template": "create_versioned_requirement",
  "parameters": {
    "req_id": "AUTH-001",
    "title": "ユーザー認証機能",
    "description": "OAuth2.0実装",
    "author": "TeamA",
    "reason": "新規機能追加",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### 重複チェックの応答形式
```json
{
  "status": "info",
  "message": "類似の可能性がある要件",
  "similar_requirements": [
    {
      "id": "AUTH-001",
      "title": "ユーザー認証機能",
      "description": "OAuth2.0を使用した安全なログイン機能",
      "match_type": ["vss", "fts"],
      "created_at": "2024-01-01"
    }
  ],
  "action": "proceed",
  "created": {
    "id": "LOGIN-001",
    "version": 1
  }
}
```

### embedding次元数の決定
- 384次元を採用（POC searchの実装に準拠）
- 選定根拠：サイズとパフォーマンスのバランス
- 将来的な長文対応も考慮

### 削除される機能
- Cypher直接実行（type: "cypher"）
- semantic_searchの外部API（内部利用のみ）
- バージョニング専用API
- グラフ深さ検証
- 循環参照検出