# Flake Graph Explorer → Architecture統合移行計画

## 概要

このドキュメントは、`bin/docs/graph/`にあるFlake Graph Explorerプロジェクトを`bin/src/architecture/{ddl,dml,dql}`へ移行するための詳細な計画と議論の記録です。

## 移行の背景と目的

### 現状の問題点

1. **責務の混在**: 現在のflakeはDML（データ操作）とDQL（データ照会）の両方の責務を持っている
2. **重複実装**: kuzu_pyやVSS関連の機能が他のプロジェクトと重複
3. **テスタビリティ**: 責務が混在しているため、単体テストが困難

### 移行の目的

1. **責務分離**: DMLとDQLを明確に分離し、単一責務の原則を徹底
2. **再利用性向上**: 共通機能をarchitecture層に集約
3. **保守性向上**: 各コンポーネントの責務を明確化

## アーキテクチャ設計原則

### Architecture READMEからの重要な指針

- **implementation**: ファイルシステムからの実装データ収集に特化（DMLのみ）
- **requirement**: 人間からの要件データ入力に特化（DMLのみ）
- **DQL**: すべてのクエリをCypherファイルとして管理（Pythonコードから分離）

## 詳細な移行計画

### 1. 現在の構造分析

```
bin/docs/graph/                         # 現在：DML/DQL混在
├── flake_graph/
│   ├── scanner.py                     # DML: flakeスキャン
│   ├── kuzu_adapter.py                # DML/DQL: DB操作全般
│   ├── vss_adapter.py                 # DML/DQL: VSS操作全般
│   ├── vss_adapter_class.py           # DML/DQL: VSS実装
│   ├── duplicate_detector.py          # DML: 重複検出
│   └── export_handler.py              # DQL: エクスポート
```

### 2. 移行後の構造（architecture/dml/implementation/）

```
architecture/dml/implementation/
├── scanner/                           # flakeスキャン機能
│   ├── flake_scanner.py              # ディレクトリスキャン
│   ├── flake_parser.py               # flake.nix解析
│   └── readme_extractor.py           # README抽出
├── analyzers/                         # 分析機能
│   ├── content_analyzer.py           # コンテンツ分析
│   ├── duplicate_analyzer.py         # 重複検出
│   └── variation_analyzer.py         # 日英バリエーション検出
├── embeddings/                        # エンベディング管理
│   ├── embedding_generator.py        # エンベディング生成
│   └── incremental_processor.py      # 増分処理
├── infrastructure/                    # インフラ層
│   ├── kuzu_writer.py               # KuzuDB書き込み専用
│   ├── vss_indexer.py               # VSSインデックス作成
│   ├── embedding_writer.py           # エンベディング永続化
│   └── batch_processor.py            # バッチ処理
├── domain/                           # ドメイン層
│   ├── entities.py                  # エンティティ定義
│   └── value_objects.py             # 値オブジェクト
└── application/                      # アプリケーション層
    ├── scan_service.py              # スキャンサービス
    ├── embedding_service.py         # エンベディングサービス
    └── analysis_service.py          # 分析サービス
```

### 3. DQL機能の移行（architecture/dql/）

```
architecture/dql/
├── implementation/                    # 実装関連クエリ
│   ├── search_by_description.cypher
│   ├── search_by_path_pattern.cypher
│   └── get_flake_details.cypher
├── similarity/                        # 類似性検索
│   ├── find_similar_implementations.cypher
│   └── get_duplicate_groups.cypher
└── export/                           # エクスポート
    └── export_implementation_summary.cypher
```

## 実装の詳細な対応表

### コアロジックの移行

| 現在の実装 | 移行先 | 変更内容 |
|-----------|--------|----------|
| `scanner.py::scan_directory()` | `scanner/flake_scanner.py::FlakeScanner.scan_directory()` | クラスベースに変更 |
| `scanner.py::_parse_flake()` | `scanner/flake_parser.py::FlakeParser.parse_flake_file()` | 独立したパーサーに |
| `scanner.py::_extract_readme()` | `scanner/readme_extractor.py::ReadmeExtractor.extract_readme_content()` | 専用クラスに分離 |

### KuzuAdapter機能の分離

| 現在のメソッド | 移行先 | 理由 |
|---------------|--------|------|
| `store_flake_with_vss_data()` | `infrastructure/kuzu_writer.py::KuzuWriter.write_flake()` | DML機能 |
| `get_flake_vss_data()` | 削除 → `dql/implementation/get_flake_details.cypher` | DQL機能 |
| `get_all_embeddings()` | 削除 → `dql/similarity/get_all_embeddings.cypher` | DQL機能 |
| `store_embedding()` | `infrastructure/embedding_writer.py::EmbeddingWriter.store_embedding()` | DML機能 |

### VSSAdapter機能の分離

| 現在のメソッド | 移行先 | 理由 |
|---------------|--------|------|
| `index_flakes()` | `application/embedding_service.py::EmbeddingService.generate_and_store()` | DML機能 |
| `search()` | 削除 → `dql/similarity/find_similar_implementations.cypher` | DQL機能 |
| `index_flakes_incremental()` | `embeddings/incremental_processor.py::IncrementalProcessor.process_incremental()` | DML機能 |
| `_should_skip_flake()` | `embeddings/incremental_processor.py::IncrementalProcessor._needs_update()` | DML機能 |

## 移行作業のフェーズ

### Phase 1: 準備作業
1. architecture/dml/implementation/ディレクトリ構造の作成
2. ドメインエンティティの定義（entities.py, value_objects.py）
3. 基本的なインフラストラクチャクラスの作成

### Phase 2: DML機能の移行
1. スキャナー機能の移行
2. エンベディング生成・永続化機能の移行
3. 重複検出・分析機能の移行
4. テストの移行と修正

### Phase 3: DQL機能の分離
1. 検索関連のPythonコードをCypherクエリに変換
2. エクスポート機能をCypherクエリに変換
3. DQL専用のCLIツール作成（必要に応じて）

### Phase 4: 統合とクリーンアップ
1. 旧コードの削除
2. 依存関係の更新
3. ドキュメントの更新

## テスト戦略

### 単体テスト
- 各クラス・メソッドに対する独立したテスト
- モックを使用した依存関係の分離

### 統合テスト
- サービス層のエンドツーエンドテスト
- 実際のKuzuDB/VSSを使用した動作確認

### 移行されるテスト

| 現在のテスト | 移行先 |
|-------------|--------|
| `test_duplicate_detection_spec.py` | `tests/unit/test_duplicate_analyzer.py` |
| `test_incremental_indexing_spec.py` | `tests/unit/test_incremental_processor.py` |
| `test_vss_persistence_spec.py` | `tests/integration/test_embedding_writer.py` |
| `test_information_export_spec.py` | 削除（DQLテストへ） |

## 期待される成果

1. **明確な責務分離**: DMLとDQLが完全に分離
2. **高い再利用性**: 他のプロジェクトから個別に利用可能
3. **優れたテスタビリティ**: 各コンポーネントが独立してテスト可能
4. **保守性の向上**: 変更の影響範囲が限定的

## リスクと対策

### リスク
1. 移行中の機能停止
2. パフォーマンスの劣化
3. 既存の依存関係の破壊

### 対策
1. 段階的な移行（新旧並行稼働）
2. パフォーマンステストの実施
3. 十分な統合テストの実施

## 結論

この移行により、Flake Graph Explorerは明確に責務分離されたアーキテクチャとなり、保守性・拡張性・再利用性が大幅に向上します。特に、DMLとDQLの分離により、各機能を独立して開発・テスト・デプロイできるようになります。