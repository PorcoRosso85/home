# Requirement Reference Guardrail POC

## 概要

要件管理システムにおいて、セキュリティ標準（ASVS等）への参照を強制するガードレール機能を提供するPOC。要件作成時に必ずセキュリティ標準との関連付けを要求し、コンプライアンスを保証します。

## 本POCの責務

### 1. **ReferenceEntityのDDL管理**
- KuzuDBにセキュリティ標準（ASVS等）を格納するReferenceEntityテーブルを定義
- requirement/graphの既存スキーマを拡張してIMPLEMENTS関係を追加
- 例外管理のためのExceptionRequestテーブルとHAS_EXCEPTION関係を管理

### 2. **ガードレール強制ロジック**
- 要件作成時にセキュリティ標準への参照を必須化
- トランザクションレベルで要件と参照の原子性を保証
- 正当な理由での例外を承認ワークフロー付きで許可

### 3. **外部POCとの統合**
- **asvs_reference POC**: ASVSデータをArrow Table形式で取得
- **embed POC**: 要件の重複検出や類似度検索機能を活用
- **requirement/graph**: 既存の要件管理システムと統合

## アーキテクチャ

```
requirement_reference_guardrail/
├── ddl/
│   └── migrations/
│       └── 3.5.0_reference_guardrails.cypher  # ReferenceEntityとIMPLEMENTS関係の定義
├── src/
│   └── guardrail/
│       ├── __init__.py                        # パッケージ初期化
│       ├── guardrail_logic.py                 # DB非依存のガードレールロジック
│       └── minimal_enforcer.py                # トランザクションレベルの強制実装
├── scripts/
│   ├── import_asvs_with_embeddings.py         # ASVSデータと埋め込みのインポート
│   ├── demo_guardrail_logic.py                # ガードレールロジックのデモ
│   ├── coverage_analysis.cypher               # カバレッジ分析クエリ集
│   └── run_coverage_analysis.py               # カバレッジ分析実行スクリプト
├── tests/
│   ├── test_minimal_enforcer.py               # 強制ロジックのテスト
│   ├── test_asvs_import.py                    # インポート機能のテスト
│   └── test_ddl_migration.py                  # DDL適用テスト
└── docs/
    ├── poc_meta_node_handover.md              # GuardrailRuleノード実装の引き継ぎ
    └── 保存されたKuzuDBドキュメント           # インポート機能の参考資料

```

## 主要機能

### 1. 要件作成時の強制チェック

```python
from guardrail.minimal_enforcer import enforce_basic_guardrails

# セキュリティ関連要件は参照なしで作成できない
result = enforce_basic_guardrails(
    conn,
    "REQ-001",
    "ユーザー認証を実装する",
    []  # 参照なし
)
# → エラー: Authentication requirements must reference ASVS V2 or NIST IA controls

# 正しい使用方法
result = enforce_basic_guardrails(
    conn,
    "REQ-001",
    "ユーザー認証を実装する",
    ["ASVS-V2.1.1", "ASVS-V2.1.7"]
)
# → 成功: 要件がASVS標準と関連付けられて作成
```

### 2. カバレッジ分析

```bash
# カバレッジ分析クエリを実行
python scripts/run_coverage_analysis.py /path/to/database

# 出力例:
# - セキュリティカテゴリ別の要件数
# - 参照なし要件の一覧
# - ASVS セクション別のカバレッジ
# - 全体的なコンプライアンス率
```

### 3. 例外管理

```python
from guardrail.minimal_enforcer import create_exception_request

# 正当な理由での標準除外申請
result = create_exception_request(
    conn,
    "REQ-LEGACY-001",
    reason="レガシーシステムとの互換性のため一時的に除外",
    mitigation="次期バージョンで標準準拠予定"
)
# → 承認待ち状態で例外申請が作成される
```

## 使用方法

### 1. DDLマイグレーション実行

```bash
# KuzuDBにスキーマを適用
cat ddl/migrations/3.5.0_reference_guardrails.cypher | kuzu-cli /path/to/database
```

### 2. ASVSデータのインポート

```bash
# ASVSデータと埋め込みベクトルをインポート
python scripts/import_asvs_with_embeddings.py /path/to/database
```

### 3. ガードレール適用例

```python
from guardrail.minimal_enforcer import enforce_basic_guardrails

# セキュリティ関連の要件を作成
result = enforce_basic_guardrails(
    conn,
    "REQ-001", 
    "ユーザー認証を実装する",
    ["ASVS-V2.1.1"]  # 適切な参照が必要
)
```

### 4. カバレージ分析

```bash
# 要件と参照のカバレージを分析
python scripts/run_coverage_analysis.py /path/to/database
```

## 依存関係

- **requirement/graph**: 要件管理システムの基盤
- **persistence/kuzu_py**: KuzuDB Python API
- **poc/asvs_reference**: ASVSデータプロバイダー（Arrow Table形式）
- **poc/embed**: 埋め込みベースの類似度検索（重複検出用）

## 技術的な特徴

### スキーマ設計

```cypher
-- セキュリティ標準を管理するエンティティ
CREATE NODE TABLE ReferenceEntity (
    id STRING PRIMARY KEY,      -- 例: "ASVS-V2.1.1"
    standard STRING,            -- 例: "ASVS"
    version STRING,             -- 例: "5.0"
    section STRING,             -- 例: "V2"
    subsection STRING,          -- 例: "2.1.1"
    title STRING,               -- 要件のタイトル
    description STRING,         -- 詳細説明
    level INT,                  -- 1, 2, 3
    category STRING,            -- "authentication", "session", etc
    embedding DOUBLE[384]       -- 意味的類似度検索用ベクトル
);

-- 要件が標準を実装することを表現
CREATE REL TABLE IMPLEMENTS (
    FROM RequirementEntity TO ReferenceEntity,
    implementation_type STRING DEFAULT 'full',
    compliance_level STRING DEFAULT 'required',
    notes STRING,
    verified_date STRING,
    evidence_uri STRING
);
```

### データインポート戦略

1. **asvs_referenceからArrow Table取得**
   ```python
   from asvs_reference import get_asvs_requirements_table
   arrow_table = get_asvs_requirements_table()
   ```

2. **embedサービスで埋め込みベクトル生成**
   ```python
   from embed import get_embeddings
   descriptions = [row['description'] for row in arrow_table]
   embeddings = get_embeddings(descriptions)
   ```

3. **KuzuDBへのバッチインポート**
   ```python
   # スクリプトを使用
   python scripts/import_asvs_with_embeddings.py /path/to/database
   ```

### トランザクション保証

要件と参照の作成は同一トランザクション内で実行され、どちらか一方だけが存在する状態を防ぎます：

```python
conn.begin()
try:
    # 1. 要件を作成
    create_requirement(...)
    
    # 2. 参照関係を作成（必須）
    create_implements_relationship(...)
    
    conn.commit()
except:
    conn.rollback()
```

## 今後の拡張可能性

- 複数のセキュリティ標準のサポート（NIST, ISO 27001等）
- 自動コンプライアンスレポート生成
- CI/CDパイプラインへの統合
- リアルタイムダッシュボード

## 開発状況

以下の機能が実装済み：

1. ✅ 要件とセキュリティ標準の関連付けスキーマ設計
2. ✅ ASVSデータのインポート機能（埋め込みベクトル付き）
3. ✅ ガードレール強制ロジック（ハードコード版）
4. ✅ カバレッジ分析機能
5. ✅ 例外管理ワークフロー

今後の実装予定：
- ⬜ GuardrailRuleノードによるデータ駆動型ルール（poc/meta_node待ち）
- ⬜ より詳細なコンプライアンスレポート
- ⬜ 他のセキュリティ標準のサポート（NIST, ISO 27001等）