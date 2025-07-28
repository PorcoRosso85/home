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
│   ├── asvs_importer.py                       # ASVSデータのインポート機能
│   ├── guardrail_enforcer.py                  # ガードレール強制ロジック
│   └── coverage_analyzer.py                   # コンプライアンスカバレッジ分析
├── tests/
│   ├── test_reference_entity_migration.py     # DDL適用テスト
│   ├── test_guardrail_enforcement.py          # 強制ロジックのテスト
│   └── test_coverage_analysis.py              # カバレッジ計算のテスト
└── docs/
    ├── kuzudb-import.md                       # KuzuDBインポート機能のドキュメント
    └── kuzudb-python-load-from.md             # Python APIのLOAD FROM機能

```

## 主要機能

### 1. 要件作成時の強制チェック

```python
# 標準参照なしでの要件作成は失敗
result = create_requirement({
    "title": "パスワード認証",
    "description": "ユーザーのパスワード認証を実装"
})
# → エラー: セキュリティ標準への参照が必要です

# 正しい使用方法
result = create_requirement_with_references(
    requirement={
        "title": "パスワード認証",
        "description": "ユーザーのパスワード認証を実装"
    },
    reference_ids=["ASVS_V2.1.1", "ASVS_V2.1.7"]
)
# → 成功: 要件がASVS標準と関連付けられて作成
```

### 2. カバレッジ分析

```python
# カテゴリ別のセキュリティ標準カバレッジを取得
coverage = analyze_coverage_by_category("authentication")
print(f"認証カテゴリのカバレッジ: {coverage['percentage']}%")
print(f"未実装項目: {coverage['missing_items']}")
```

### 3. 例外管理

```python
# 正当な理由での標準除外申請
exception = request_exception(
    requirement_data={...},
    justification="レガシーシステムとの互換性のため一時的に除外",
    mitigation_plan="次期バージョンで標準準拠予定"
)
# → 承認待ち状態で例外申請が作成される
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
    id STRING PRIMARY KEY,      -- 例: "ASVS_V2.1.1"
    standard STRING,            -- 例: "OWASP ASVS"
    version STRING,             -- 例: "5.0"
    section STRING,             -- 例: "V2.1.1"
    description STRING,
    level INT,                  -- 1, 2, 3
    category STRING             -- "authentication", "session", etc
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
   arrow_table = get_asvs_requirements_table()
   ```

2. **KuzuDBへの直接インポート**
   ```python
   conn.execute("COPY ReferenceEntity FROM arrow_table")
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

本POCは現在開発中です。以下の機能を実装予定：

1. ✅ 要件とセキュリティ標準の関連付けスキーマ設計
2. ⬜ ASVSデータのインポート機能
3. ⬜ ガードレール強制ロジック
4. ⬜ カバレッジ分析機能
5. ⬜ 例外管理ワークフロー