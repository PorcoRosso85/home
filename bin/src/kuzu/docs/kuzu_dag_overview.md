# KuzuDBによる未来志向DAG管理システム

## 1. 概要と背景

### なぜKuzuDBで未来を管理するのか

従来のソフトウェア開発では、Gitが過去の記録を管理し、プロジェクト管理ツールが未来の計画を管理してきました。しかし、この二元管理には根本的な問題があります：

- **Git**: 過去の変更履歴を完璧に記録するが、未来の計画には無力
- **従来のツール**: 未来の計画を管理するが、論理的な依存関係の検証が困難

KuzuDBを使用することで、**未来の計画をグラフ構造として管理**し、以下を実現します：

- 計画間の依存関係を明示的にモデル化
- CypherクエリによるDAGの整合性検証
- Version-URIベースの軽量な状態追跡

### Bauplanとの違い

Bauplanプロジェクトは一時的なグラフ構造でコードを検証しますが、我々のアプローチは異なります：

| 側面 | Bauplan | 我々のアプローチ |
|------|---------|-----------------|
| グラフの永続性 | 一時的（検証時のみ） | 永続的（計画期間中） |
| 主な用途 | コード構造の検証 | 未来の計画管理 |
| ライフサイクル | ビルド時に生成・破棄 | 計画作成から完了まで保持、完了後削除 |
| 焦点 | 現在のコードの整合性 | 未来の変更の依存関係 |

### 従来の課題と解決

従来のプロジェクト管理には以下の課題がありました：

1. **計画の論理的整合性が取れない**
   - タスクAがタスクBに依存することを記述しても、循環依存を検出できない
   - 解決: CypherクエリでDAGの整合性を常時検証

2. **依存関係の発見が遅い**
   - 実装段階になって初めて依存関係の問題が発覚
   - 解決: 計画段階でグラフ構造として可視化・検証

3. **計画と実装の乖離**
   - 計画と実際のコード変更の対応関係が不明確
   - 解決: LocationURIで計画と実装を統一的に管理

## 2. コアコンセプト

### Version-URIが中心

このシステムの中核は**シンプルさ**です：

```
VersionState --TRACKS_STATE_OF_LOCATED_ENTITY--> LocationURI
```

- **VersionState**: タイムスタンプ付きの状態（計画、進行中、完了など）
- **LocationURI**: 変更対象の場所を表す永続的な識別子

この単純な関係により、「いつ」「どこで」「何が起きるか」を追跡します。

### Code/Requirementは詳細情報

LocationURIに対して、必要に応じて詳細情報を付加します：

```
LocationURI --LOCATED_WITH--> CodeEntity
LocationURI --LOCATED_WITH_REQUIREMENT--> RequirementEntity
```

これにより：
- 必要最小限の情報から開始可能
- 詳細が明らかになるにつれて情報を追加
- 不要な複雑性を回避

### エフェメラルな未来管理

完了した計画は積極的に削除します：

1. **計画フェーズ**: グラフに未来の状態を記録
2. **実行フェーズ**: 進捗に応じてVersionStateを更新
3. **完了フェーズ**: Gitにコミット後、グラフから削除

この「エフェメラル（一時的）」なアプローチにより：
- データベースの肥大化を防止
- 常に「生きている」計画のみを管理
- クエリパフォーマンスを維持

## 3. スキーマ設計

### ノードテーブル

```cypher
-- 変更対象の場所を表す中心的なエンティティ
CREATE NODE TABLE LocationURI (
    id STRING PRIMARY KEY  -- 例: "file://src/main.rs#function:process_data"
);

-- バージョン管理の状態
CREATE NODE TABLE VersionState (
    id STRING PRIMARY KEY,      -- 例: "v1.2.3-planning"
    timestamp STRING,           -- ISO 8601形式
    description STRING          -- 状態の説明
);

-- コードエンティティの詳細情報
CREATE NODE TABLE CodeEntity (
    persistent_id STRING PRIMARY KEY,  -- 永続的な識別子
    name STRING,                       -- エンティティ名
    type STRING,                       -- 'function', 'class', 'module'など
    signature STRING                   -- 関数シグネチャなど
);

-- 要件エンティティ
CREATE NODE TABLE RequirementEntity (
    id STRING PRIMARY KEY,      -- 例: "req_add_auth_2024"
    title STRING,               -- 要件のタイトル
    description STRING          -- 詳細な説明
);
```

### リレーションテーブル

```cypher
-- バージョン状態が追跡する場所
CREATE REL TABLE TRACKS_STATE_OF_LOCATED_ENTITY (
    FROM VersionState TO LocationURI
);

-- 場所に関連付けられたコードエンティティ
CREATE REL TABLE LOCATED_WITH (
    FROM LocationURI TO CodeEntity
);

-- 場所に関連付けられた要件
CREATE REL TABLE LOCATED_WITH_REQUIREMENT (
    FROM LocationURI TO RequirementEntity
);

-- 要件間の依存関係（DAG構造）
CREATE REL TABLE DEPENDS_ON (
    FROM RequirementEntity TO RequirementEntity
);

-- コード間の参照関係
CREATE REL TABLE REFERENCES_CODE (
    FROM CodeEntity TO CodeEntity
);
```

### 使用例

#### 1. 新しい計画の追加

```cypher
-- LocationURIの作成
CREATE (:LocationURI {id: 'file://src/auth/login.rs#function:authenticate'});

-- VersionStateの作成
CREATE (:VersionState {
    id: 'v2.0.0-auth-planning',
    timestamp: '2024-12-18T10:00:00Z',
    description: '認証機能の追加計画'
});

-- 関係の作成
MATCH (v:VersionState {id: 'v2.0.0-auth-planning'})
MATCH (l:LocationURI {id: 'file://src/auth/login.rs#function:authenticate'})
CREATE (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(l);
```

#### 2. DAGの整合性検証

```cypher
-- 循環依存の検出
MATCH path = (r1:RequirementEntity)-[:DEPENDS_ON*]->(r2:RequirementEntity)
WHERE r1 = r2
RETURN path;
```

#### 3. 完了した計画の削除

```cypher
-- 完了したVersionStateとその関連を削除
MATCH (v:VersionState {id: 'v2.0.0-auth-planning'})-[r:TRACKS_STATE_OF_LOCATED_ENTITY]->(l:LocationURI)
WHERE v.description CONTAINS '完了'
DELETE r, v;
```

### グラフの視覚化例

```
[VersionState: v2.0.0-planning]
        |
        | TRACKS_STATE_OF_LOCATED_ENTITY
        v
[LocationURI: file://src/main.rs]
        |                    |
        | LOCATED_WITH       | LOCATED_WITH_REQUIREMENT
        v                    v
[CodeEntity: main_function] [RequirementEntity: req_refactor_2024]
                                    |
                                    | DEPENDS_ON
                                    v
                            [RequirementEntity: req_api_update_2024]
```

## まとめ

KuzuDBによる未来志向DAG管理システムは、以下の特徴を持ちます：

1. **シンプルさ**: Version-URIを中心とした最小限の構造
2. **柔軟性**: 必要に応じて詳細情報を追加
3. **検証可能性**: CypherクエリによるDAG整合性の常時検証
4. **軽量性**: エフェメラルな管理による永続的な軽量化

このアプローチにより、Gitが管理する「過去」と、KuzuDBが管理する「未来」が明確に分離され、それぞれの強みを最大限に活用できます。