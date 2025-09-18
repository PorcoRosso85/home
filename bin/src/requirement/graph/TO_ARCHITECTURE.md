# requirement/graph アーキテクチャ移行計画

## 概要

現在のrequirement/graphディレクトリをDDL/DML/DQL責務に基づいて再構築する計画書。
データベース操作の責務を明確に分離し、保守性と拡張性を向上させる。

## 現状の課題

1. **責務の混在**: infrastructure/配下に異なる責務（スキーマ管理、データ操作、検索）が混在
2. **検索機能の分散**: search_adapter.pyにDMLとDQLの両方の責務が存在
3. **クエリの散在**: query/配下にDDL/DML/DQLが未分類で配置
4. **再利用性の低下**: 各機能が密結合しており、個別の再利用が困難

## 移行後のディレクトリ構造

```
requirement/graph/
├── ddl/                                    # Data Definition Language
├── dml/                                    # Data Manipulation Language
├── dql/                                    # Data Query Language
├── domain/                                 # ビジネスロジック（変更なし）
├── application/                            # アプリケーション層
├── infrastructure/                         # 共通基盤
└── e2e/                                   # E2Eテスト（変更なし）
```

## DDL（Data Definition Language）

スキーマ定義、管理、検証に関する責務を集約。

### ddl/schema/
```
ddl/schema/
├── migrations/                             # 既存のddl/migrations/を移動
│   ├── 3.1.0_initial.cypher
│   ├── 3.2.0_current.cypher
│   ├── 3.2.0_remove_has_version.cypher
│   ├── 3.3.0_radical_simplification.cypher
│   ├── 3.3.0_simplified.cypher
│   ├── 3.4.0_search_integration.cypher
│   └── README.md
├── manager.py                              # infrastructure/ddl_schema_manager.pyから移動
│   └── DDLSchemaManager
│       ├── __init__(self, connection, schema_dir: str)
│       ├── apply_schema(self, version: str) -> bool
│       ├── get_current_version(self) -> Optional[str]
│       ├── validate_schema(self) -> bool
│       └── rollback_schema(self, target_version: str) -> bool
└── apply.py                                # infrastructure/apply_ddl_schema.pyから移動
    └── apply_ddl_schema(db_path: Optional[str], create_test_data: bool) -> bool
```

### ddl/validation/
```
ddl/validation/
├── circular_reference_detector.py          # infrastructure/circular_reference_detector.pyから移動
│   ├── CircularReferenceDetector
│   │   ├── detect_cycles(self, dependencies: List[Tuple[str, str]]) -> Dict[str, any]
│   │   └── find_all_cycles(self, dependencies: List[Tuple[str, str]]) -> List[List[str]]
│   ├── create_cypher_cycle_query() -> str
│   ├── validate_with_kuzu(connection) -> Dict[str, any]
│   └── get_cycle_impact_score(cycle_length: int) -> int
└── graph_depth_validator.py                # infrastructure/graph_depth_validator.pyから移動
    └── GraphDepthValidator
        ├── __init__(self, max_depth: int = 10)
        ├── validate(self, connection) -> ValidationResult
        └── get_max_depth(self, connection, node_id: str) -> int
```

## DML（Data Manipulation Language）

データの作成、更新、削除、インデックス管理に関する責務を集約。

### dml/repositories/
```
dml/repositories/
├── kuzu_repository.py                      # infrastructure/kuzu_repository.pyから移動
│   └── KuzuRepository
│       ├── __init__(self, connection)
│       ├── create_requirement(self, requirement: Dict) -> Result
│       ├── update_requirement(self, id: str, updates: Dict) -> Result
│       ├── delete_requirement(self, id: str) -> Result
│       ├── add_dependency(self, from_id: str, to_id: str) -> Result
│       ├── remove_dependency(self, from_id: str, to_id: str) -> Result
│       └── bulk_insert(self, requirements: List[Dict]) -> Result
└── jsonl_repository.py                     # infrastructure/jsonl_repository.pyから移動
    ├── create_jsonl_repository(file_path: str) -> Dict
    │   ├── ensure_file_exists() -> None
    │   ├── save(decision: Decision) -> DecisionResult
    │   ├── find(decision_id: str) -> DecisionResult
    │   ├── find_all() -> List[Decision]
    │   ├── update(decision: Decision) -> DecisionResult
    │   └── delete(decision_id: str) -> DecisionResult
    └── JSONLRepository (クラスベース実装案)
```

### dml/indexing/
```
dml/indexing/
├── vss_indexer.py                          # search_adapter.pyのDML部分から分離
│   └── VSSIndexer
│       ├── __init__(self, db_path: str, connection=None)
│       ├── add_requirement(self, id: str, title: str, content: str) -> None
│       ├── update_requirement(self, id: str, title: str, content: str) -> None
│       ├── delete_requirement(self, id: str) -> None
│       └── rebuild_index(self) -> bool
├── fts_indexer.py                          # search_adapter.pyのDML部分から分離
│   └── FTSIndexer
│       ├── __init__(self, db_path: str, connection=None)
│       ├── add_requirement(self, id: str, title: str, content: str) -> None
│       ├── update_requirement(self, id: str, title: str, content: str) -> None
│       ├── delete_requirement(self, id: str) -> None
│       └── rebuild_index(self) -> bool
└── unified_indexer.py                      # SearchAdapterのadd_to_index部分
    └── UnifiedIndexer
        ├── __init__(self, vss_indexer: VSSIndexer, fts_indexer: FTSIndexer)
        ├── add_to_index(self, requirement: Dict[str, Any]) -> bool
        ├── update_in_index(self, requirement: Dict[str, Any]) -> bool
        ├── remove_from_index(self, id: str) -> bool
        └── sync_all_indexes(self) -> bool
```

### dml/queries/
```
dml/queries/                                # query/dml/を移動
├── create_requirement.cypher
├── create_versioned_requirement.cypher
├── add_dependency.cypher
├── add_dependency_template.cypher
└── README.md
```

## DQL（Data Query Language）

データの検索、分析、トラバーサルに関する責務を集約。

### dql/search/
```
dql/search/
├── vss/
│   ├── adapter.py                          # VSSSearchAdapterのDQL部分
│   │   └── VSSAdapter
│   │       ├── __init__(self, db_path: str, connection=None)
│   │       ├── search_similar(self, query: str, k: int = 10) -> List[Dict[str, Any]]
│   │       ├── generate_embedding(self, text: str) -> Optional[List[float]]
│   │       └── is_available(self) -> bool
│   └── query_builder.py
│       ├── build_similarity_query(query: str, k: int) -> str
│       ├── build_vector_search_query(embedding: List[float], k: int) -> str
│       └── build_cosine_distance_query(vec1: List[float], vec2: List[float]) -> str
│
├── fts/
│   ├── adapter.py                          # FTSSearchAdapterのDQL部分
│   │   └── FTSAdapter
│   │       ├── __init__(self, db_path: str, connection=None)
│   │       ├── search_keyword(self, query: str, k: int = 10) -> List[Dict[str, Any]]
│   │       └── is_available(self) -> bool
│   └── query_builder.py
│       ├── build_keyword_query(keywords: str, k: int) -> str
│       ├── build_fulltext_query(text: str, fields: List[str]) -> str
│       └── build_phrase_query(phrase: str) -> str
│
├── hybrid/
│   ├── adapter.py                          # SearchAdapterのhybrid search部分
│   │   └── HybridSearchAdapter
│   │       ├── __init__(self, vss_adapter: VSSAdapter, fts_adapter: FTSAdapter)
│   │       ├── search_hybrid(self, query: str, k: int = 10) -> List[Dict[str, Any]]
│   │       ├── merge_results(self, vss_results: List, fts_results: List) -> List
│   │       └── normalize_scores(self, results: List) -> List
│   └── ranker.py
│       ├── reciprocal_rank_fusion(results_lists: List[List], k: int = 60) -> List
│       ├── weighted_score_fusion(vss_results: List, fts_results: List, vss_weight: float = 0.7) -> List
│       └── borda_count_fusion(results_lists: List[List]) -> List
│
└── duplicate/
    ├── detector.py                         # SearchAdapterのcheck_duplicates部分
    │   └── DuplicateDetector
    │       ├── __init__(self, search_adapter: HybridSearchAdapter)
    │       ├── check_duplicates(self, text: str, k: int = 5, threshold: float = 0.5) -> List[Dict[str, Any]]
    │       ├── calculate_similarity(self, text1: str, text2: str) -> float
    │       └── filter_by_threshold(self, results: List, threshold: float) -> List
    └── threshold_manager.py
        ├── get_threshold_for_domain(domain: str) -> float
        ├── adjust_threshold_dynamically(history: List[float]) -> float
        └── validate_threshold(value: float) -> bool
```

### dql/graph/
```
dql/graph/
├── traversal.py                            # グラフ探索クエリ
│   ├── find_dependencies(connection, requirement_id: str, depth: int = -1) -> List[Dict]
│   ├── find_dependents(connection, requirement_id: str, depth: int = -1) -> List[Dict]
│   ├── find_connected_components(connection, requirement_id: str) -> List[Set[str]]
│   └── find_shortest_path(connection, from_id: str, to_id: str) -> Optional[List[str]]
├── analytics.py                            # グラフ分析クエリ
│   ├── calculate_impact_score(connection, requirement_id: str) -> float
│   ├── find_critical_path(connection, from_id: str, to_id: str) -> List[str]
│   ├── detect_bottlenecks(connection, threshold: int = 5) -> List[Dict]
│   └── calculate_centrality(connection, algorithm: str = "betweenness") -> Dict[str, float]
└── version.py                              # バージョン関連クエリ
    ├── get_requirement_history(connection, requirement_id: str) -> List[Dict]
    ├── get_version_diff(connection, req_id: str, v1: str, v2: str) -> Dict
    ├── get_requirement_at_timestamp(connection, req_id: str, timestamp: datetime) -> Optional[Dict]
    └── list_all_versions(connection, requirement_id: str) -> List[str]
```

### dql/interfaces/
```
dql/interfaces/
├── unified_query.py                        # infrastructure/unified_query_interface.pyから移動
│   └── UnifiedQueryInterface
│       ├── __init__(self, connection)
│       ├── execute_query(self, query: str, params: Dict = None) -> Result
│       ├── prepare_parameters(self, params: Dict) -> Dict
│       └── validate_query(self, query: str) -> bool
└── query_loader.py                         # query/loader.pyから移動
    └── QueryLoader
        ├── __init__(self, base_path: str)
        ├── load_query(self, name: str) -> str
        ├── get_all_queries(self) -> Dict[str, str]
        └── reload_queries(self) -> None
```

### dql/queries/
```
dql/queries/                                # query/dql/を移動
├── find_dependencies.cypher
├── find_dependencies_simple.cypher
├── find_requirement.cypher
├── get_dependencies.cypher
├── get_requirement_at_timestamp.cypher
├── get_requirement_history.cypher
├── get_requirement_history_v2.cypher
├── get_requirement_versions.cypher
├── get_version_diff.cypher
├── list_all_versions.cypher
├── list_requirements.cypher
├── search_requirements_by_uri.cypher
└── README.md
```

## Infrastructure（共通基盤）

横断的関心事のみを管理。

```
infrastructure/
├── database/
│   ├── factory.py                          # database_factory.pyから移動
│   │   ├── create_database(path: str) -> Database
│   │   ├── create_connection(path: str) -> Connection
│   │   └── DatabaseFactory
│   │       ├── __init__(self, config: Dict)
│   │       └── create(self, db_type: str) -> Database
│   └── connection_pool.py                  # 新規：接続プール管理
│       └── ConnectionPool
│           ├── __init__(self, db_path: str, max_connections: int = 10)
│           ├── get_connection(self) -> Connection
│           ├── release_connection(self, conn: Connection) -> None
│           └── close_all(self) -> None
│
├── logging/
│   ├── logger.py                           # 既存
│   │   ├── debug(category: str, message: str)
│   │   ├── info(category: str, message: str)
│   │   ├── warn(category: str, message: str)
│   │   └── error(category: str, message: str)
│   └── wrapper.py                          # logger_wrapper.pyから移動
│       └── LoggerWrapper
│           ├── __init__(self, logger)
│           ├── wrap_method(self, method, method_name: str)
│           └── log_execution(self, method_name: str, args, kwargs, result, error)
│
└── variables/                              # 既存のまま
    ├── __init__.py
    ├── constants.py
    ├── env.py
    ├── hierarchy_env.py
    ├── test_env.py
    └── test_hierarchy_env.py
```

## Application層の変更

```
application/
├── __init__.py
├── error_handler.py                        # 既存のまま
├── template_processor.py                   # 既存のまま
└── templates/                              # 既存のまま
    ├── __init__.py
    ├── search_requirements.py
    └── README.md
```

## 移行戦略

### Phase 1: 準備（リスク: 低）
1. 新規ディレクトリ構造の作成
2. 移行スクリプトの作成
3. テストの準備

### Phase 2: DDL移行（リスク: 中）
1. ddl/schema/への移行
2. ddl/validation/への移行
3. 既存参照の更新
4. テスト実行

### Phase 3: DML移行（リスク: 高）
1. dml/repositories/への移行
2. dml/indexing/への分離（search_adapter.pyの分割）
3. dml/queries/への移行
4. 統合テスト

### Phase 4: DQL移行（リスク: 高）
1. dql/search/への分離（search_adapter.pyの分割）
2. dql/graph/への新規実装
3. dql/interfaces/への移行
4. dql/queries/への移行
5. E2Eテスト

### Phase 5: クリーンアップ（リスク: 低）
1. 旧ファイルの削除
2. importパスの最適化
3. ドキュメントの更新

## 移行による利点

1. **責務の明確化**: DDL/DML/DQLが完全に分離され、各モジュールの役割が明確
2. **保守性の向上**: 変更の影響範囲が限定され、保守が容易
3. **再利用性の向上**: 各コンポーネントが独立して再利用可能
4. **テスタビリティ**: 単一責務により単体テストが書きやすい
5. **拡張性**: 新機能追加時の配置場所が明確

## リスクと対策

### リスク
1. **既存コードの破壊**: 大規模なリファクタリングによる機能の破損
2. **インポートパスの混乱**: 多数のファイル移動によるimportエラー
3. **テストの失敗**: ファイルパスに依存したテストの失敗

### 対策
1. **段階的移行**: 一度にすべてを移行せず、段階的に実施
2. **自動化ツール**: importパス更新の自動化スクリプト作成
3. **包括的テスト**: 各フェーズ後の徹底的なテスト実行
4. **ロールバック計画**: 各フェーズでのロールバック手順の準備

## 次のステップ

1. この計画のレビューと承認
2. 移行スクリプトの作成
3. Phase 1の実施