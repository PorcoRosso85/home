# 削除候補テスト一覧

## 削除基準：「リファクタリングの壁」原則
> **「もし、実装コードが壁の向こう側にあって全く見えないとしたら、このテストは書けるか？」**

- 実装詳細を知らなければ書けないテスト
- 公開APIの振る舞いではなく内部構造をテストしているもの
- モックのみで実際の動作を保証しないテスト
- ロジックを含まない自明なコードのテスト

## test_versioning_unit.py
- `test_version_service_functions_exist` - 関数の存在確認のみ
- `test_versioned_cypher_executor_creation` - インスタンス作成の確認のみ
- `test_versioning_executor_integration` - callableかどうかの確認のみ
- `test_versioning_metadata_structure` - 辞書のキー存在確認のみ
- `test_create_query_detection` - 正規表現マッチングのみ
- `test_update_query_detection` - 正規表現マッチングのみ

## test_simple_versioning.py
- `test_version_service_creation` - サービスのキー存在確認のみ

## test_scoring_service_migration.py
- `test_違反スコア定義はドメイン層に移行される` - ImportError期待
- `test_スコア計算ロジックはドメイン層で実装される` - ImportError期待
- `test_ドメイン定義は純粋なデータ構造` - 内部実装（辞書の型）テスト
- `test_ドメイン層は純粋な関数で構成される` - モジュール内部の文字列検索

## test_layer_refactoring.py
- `test_違反スコア計算はドメイン層に存在する` - ImportError期待
- `test_摩擦計算ルールはドメイン層に存在する` - ImportError期待
- `test_ドメイン層は技術詳細に依存しない` - 実装詳細（__tablename__属性）テスト
- `test_アプリケーション層はドメイン層に依存する` - dirとgetattrで内部構造検査
- `test_外部サービスとの連携はアプリケーション層の責務` - モックのみで無意味

## test_priority_numeric_only.py
- `test_priority_mapper_does_not_exist` - ファイルの非存在確認
- `test_api_v2_does_not_exist` - ファイルの非存在確認
- `test_no_string_priority_in_schema` - スキーマ内の文字列検索
- `test_friction_detector_uses_numeric_only` - ソースコード内の文字列検索
- `test_scoring_definitions_numeric_only` - メッセージ内の文字列検索

## test_priority_refactoring.py
- `test_priority_mapper_not_exists` - ファイルの非存在確認
- `test_no_high_medium_low_in_core` - 文字列検索のみ

## infrastructure/test_variables.py
- `test_定数は読み取り専用` - 定数の再代入テスト（自明）

## domain/test_constraints.py
- `test_パフォーマンス要件なし_警告` - 内部実装をテスト内で定義
- `test_セキュリティ要件なし_エラー` - 内部実装をテスト内で定義

## domain/test_decision.py
- `test_create_decision_valid_input_returns_decision_object` - オブジェクト初期化の確認のみ

## domain/test_embedder.py
- `test_create_embedding_valid_text_returns_normalized_vector` - 内部実装（正規化）テスト
- `test_create_embedding_same_input_returns_same_output` - 決定的動作の実装詳細テスト

## domain/test_types.py
- **ファイル全体を削除** - 全テストがTypedDict構造の初期化確認のみ

## domain/test_version_tracking.py
- `test_create_version_id_generates_unique_id` - time.sleepに依存した脆弱なテスト
- `test_create_location_uri_generates_standard_uri` - 文字列フォーマットの実装詳細

## application/test_autonomous_decomposer.py
- `create_mock_llm_hooks` - テストヘルパー関数（テストではない）
- `create_mock_llm_hooks_with_connection` - テストヘルパー関数（テストではない）

## application/test_requirement_service.py
- `test_重複要件_類似度90パーセント以上_警告` - モック実装をテスト
- `test_重複要件_同一内容別表現_エラー` - モック実装をテスト
- `test_create_requirement_hierarchy_creates_parent_of_relation` - TODO付き、不完全な実装
- `test_find_abstract_requirement_from_implementation_returns_vision` - TODO付き、最小限のアサーション
- `test_hierarchy_depth_limit_prevents_deep_nesting` - TODO付き、機能未実装を認識

## infrastructure/test_cypher_executor.py
- `test_parse_cypher_statements_parses_multiple_statements` - プライベートメソッドのテスト

## infrastructure/test_database_factory.py
- `test_database_factory_singleton_returns_same_instance` - シングルトンパターンの実装詳細
- `test_ensure_database_exists_already_exists_does_not_recreate` - 内部状態（初期化フラグ）テスト

## infrastructure/test_ddl_schema_manager.py
- `test_generate_drop_statement_creates_valid_drop_statement` - プライベートメソッドのテスト
- `test_parse_procedure_args_handles_complex_types` - プライベートメソッドのテスト
- `test_parse_procedure_args_handles_edge_cases` - プライベートメソッドのテスト
- `test_parse_schema_detects_query_types` - 内部パース処理のテスト

## infrastructure/test_kuzu_repository.py
- `test_register_udfs_completes_without_error` - エラーが発生しないことのみ確認

## infrastructure/test_main_udf_integration.py
- `test_udf_registration_mechanics_are_correct` - @skip済みテスト

## infrastructure/test_query_validator.py
- `test_determine_query_type_selects_correct_type` - 内部実装（クエリタイプ判定）テスト

## infrastructure/test_unified_query_interface.py
- `test_parse_cypher_statements_splits_correctly` - プライベートメソッドのテスト

## infrastructure/variables/test_env.py
- `test_skip_destructive_operations_can_be_controlled` - 環境変数の存在確認のみ
- `test_external_llm_is_disabled_by_default` - 環境変数のデフォルト値確認のみ

## 新基準による追加削除候補（ファイル全体削除）

### test_scoring_normalized.py
- **ファイル全体を削除** - 未実装の内部ドメインモデルの詳細仕様（TDD Red）

### test_scoring_rules.py  
- **ファイル全体を削除** - 未実装の内部ドメイン層の詳細仕様（TDD Red）

### test_executive_simulation.py
- **ファイル全体を削除** - 未実装の内部コンポーネントの動作テスト

### test_realtime_friction_detection.py
- **ファイル全体を削除** - 未実装機能（すでにskip済み）

### test_semantic_contradiction_detection.py
- **ファイル全体を削除** - 未実装機能の内部実装詳細（すでにskip済み）

### test_technical_debt_lifecycle.py
- **ファイル全体を削除** - 未実装機能（すでにskip済み）

## 新基準による追加削除候補（その2）

### test_kuzu_json_extension.py
- **ファイル全体を削除** - フレームワーク（KuzuDB）の機能テスト

### test_no_hierarchy_assumption.py
- **ファイル全体を削除** - 単純な文字列検索のみ（自明なコード）

### test_rgl_specification.py
- **ファイル全体を削除** - ファイル存在確認のみ（自明なコード）

### test_rgl_detailed_specification.py
- **ファイル全体を削除** - 文字列パターン検索のみ（自明なコード）

### test_schema_application_resilience.py
- **ファイル全体を削除** - 全テストがskip済み（価値なし）

### test_schema_code_consistency.py
- **ファイル全体を削除** - 静的な文字列チェックのみ（自明なコード）

### test_location_uri_hierarchy.py
- **ファイル全体を削除** - 全テストがskip済み（価値なし）

### test_pm_requirements.py
- **ファイル全体を削除** - テストコードではない（データ定義のみ）

## 「リファクタリングの壁」原則による追加削除候補

### 実装詳細に依存するE2E/統合テスト（ファイル全体削除）

#### test_e2e_startup_cto_journey.py
- **ファイル全体を削除** - リポジトリの内部構造（connection属性）やQueryResultの内部APIに依存

#### test_e2e_team_friction_scenarios.py
- **ファイル全体を削除** - 同様に内部実装の詳細に依存

#### test_friction_detection_integration.py
- **ファイル全体を削除** - 摩擦検出の内部データ構造に依存

#### application/test_decision_service.py
- **ファイル全体を削除** - テスト用スキーマセットアップで内部実装を直接操作

### domain層の実装詳細テスト

#### domain/test_embedder.py（全テスト削除済み）
- すでに個別テスト削除対象だが、実装詳細（正規化アルゴリズム）に依存

#### domain/test_version_tracking.py（全テスト削除済み）
- すでに個別テスト削除対象だが、IDフォーマットなど実装詳細に依存

### infrastructure層の不適切なテスト

#### infrastructure/test_graph_validators.py
- **ファイル全体を削除** - 実装クラスを直接import、内部構造に依存

#### infrastructure/test_custom_procedures.py（部分削除）
- 多くのテストがモッククラスに依存、実際のDB統合をテストしていない

#### infrastructure/test_requirement_validator.py（部分削除）
- 検証メソッドの名前や返り値の内部構造に依存

## サマリー

### 削除対象ファイル数：26ファイル
- TDD Redフェーズの未実装テスト：2ファイル
- skip済みテスト：6ファイル
- 実装詳細テスト：14ファイル
- E2E/統合だが実装詳細に依存：4ファイル

### 部分削除対象：約50個のテストメソッド
- プライベートメソッドのテスト
- 実装詳細（シングルトン、内部状態）のテスト
- モックのみのテスト
- 自明なコードのテスト

### 保持すべきテスト（「壁」原則に合格）
- application/test_friction_scoring.py
- application/test_optimization_features.py  
- application/test_scoring_service.py
- domain/test_constraints.py
- domain/test_decision.py
- infrastructure/test_jsonl_repository.py
- infrastructure/test_apply_ddl_schema.py