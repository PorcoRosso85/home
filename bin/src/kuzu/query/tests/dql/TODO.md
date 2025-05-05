# 階層型トレーサビリティモデルの機能とファイルパス対応表

| 機能 | DQL ファイルパス | テスト実装用 TS ファイル | この機能追加で達成できる目的 | 完了 |
|------|------------|------------|------------|------|
| 要件とコードの階層関係をLocationURIで一元管理 | /home/nixos/bin/src/kuzu/query/tests/dql/basic_queries.cypher | /home/nixos/bin/src/kuzu/query/tests/sample/test_hierarchy_relation.ts | 複雑な要件とコードの階層構造を統一的に管理し、ナビゲーションを容易にする | ✅ |
| 要件から検証方法（テスト）の双方向トレーサビリティ | /home/nixos/bin/src/kuzu/query/tests/dql/exclusive_relation_queries.cypher | /home/nixos/bin/src/kuzu/query/tests/sample/test_verification_traceability.ts | 要件から検証方法、検証方法から要件へと双方向に追跡でき、検証漏れを防止する | ✅ |
| 要件からコード実装への双方向トレーサビリティ | /home/nixos/bin/src/kuzu/query/tests/dql/implementation_traceability_queries.cypher | /home/nixos/bin/src/kuzu/query/tests/sample/test_implementation_traceability.ts | 要件の実装状況を把握し、未実装要件を検出できる | ✅ |
| テスト名・説明による要件の文書化 | /home/nixos/bin/src/kuzu/query/tests/dql/exclusive_relation_queries.cypher | /home/nixos/bin/src/kuzu/query/tests/sample/test_documentation.ts | テストコード自体が仕様書として機能し、ドキュメントの一貫性を保つ | ✅ |
| バージョン管理によるすべての要素の変更履歴追跡 | /home/nixos/bin/src/kuzu/query/tests/dql/version_queries.cypher | /home/nixos/bin/src/kuzu/query/tests/sample/test_version_queries.ts | 時間経過による変更を追跡し、任意の時点での状態を復元できる | ✅ |
| LocationURI階層を通じた要件構造の柔軟な表現 | /home/nixos/bin/src/kuzu/query/tests/dql/version_queries.cypher | /home/nixos/bin/src/kuzu/query/tests/sample/test_location_hierarchy.ts | 複雑な要件階層を表現し、大規模プロジェクトの構造化が可能になる |  |
| 依存関係の分析と影響範囲の可視化 | /home/nixos/bin/src/kuzu/query/tests/dql/dependency_analysis_queries.cypher | /home/nixos/bin/src/kuzu/query/tests/sample/test_dependency_analysis.ts | 変更の影響範囲を把握し、リスク評価や適切なテスト範囲の特定ができる | ✅ |
| 実装・テストの進捗状況の集計と分析 | /home/nixos/bin/src/kuzu/query/tests/dql/version_queries.cypher | /home/nixos/bin/src/kuzu/query/tests/sample/test_progress_analysis.ts | プロジェクトの進捗を正確に把握し、適切なリソース配分や計画調整ができる | ✅ |
| 要件カバレッジの測定と可視化 | /home/nixos/bin/src/kuzu/query/tests/dql/exclusive_relation_queries.cypher | /home/nixos/bin/src/kuzu/query/tests/sample/test_coverage_measurement.ts | 要件の実装・検証カバレッジを数値化し、品質保証の指標として活用できる |  |
| 外部参照との関係性の管理 | /home/nixos/bin/src/kuzu/query/tests/dql/version_queries.cypher | /home/nixos/bin/src/kuzu/query/tests/sample/test_external_reference.ts | 外部APIや依存ライブラリとの関係を明確にし、外部変更の影響を把握できる |  |
| 特定バージョン時点での全要件・全コードの状態復元 | /home/nixos/bin/src/kuzu/query/tests/dql/version_queries.cypher | /home/nixos/bin/src/kuzu/query/tests/sample/test_version_state_restore.ts | 過去の任意の時点での全体像を再現し、比較分析や問題追跡が可能になる |  |
| 孤立実装・要件の検出と防止 | /home/nixos/bin/src/kuzu/query/tests/dql/exclusive_relation_queries.cypher | /home/nixos/bin/src/kuzu/query/tests/sample/test_exclusive_relations.ts | 未紐付けの実装や要件を検出し、トレーサビリティの完全性を確保する | ✅ |
| テスト実行結果と要件の充足状況の紐付け | /home/nixos/bin/src/kuzu/query/tests/dql/exclusive_relation_queries.cypher | /home/nixos/bin/src/kuzu/query/tests/sample/test_result_binding.ts | テスト実行結果から要件の達成状況を直接把握でき、品質評価が容易になる |  |
| 循環依存の検出と防止 | 追加実装が必要 | /home/nixos/bin/src/kuzu/query/tests/sample/test_circular_dependency.ts | 循環参照による設計の複雑化やデッドロックを防止し、システムの安定性を高める |  |
| 動く設計書としての一貫性維持 | /home/nixos/bin/src/kuzu/query/tests/dql/version_queries.cypher | /home/nixos/bin/src/kuzu/query/tests/sample/test_living_documentation.ts | ドキュメントとコードの乖離をなくし、常に最新の設計情報を維持できる |  |
| 必須プロパティの検証 | 追加実装が必要 | /home/nixos/bin/src/kuzu/query/tests/sample/test_property_constraints.ts | データの完全性を保証し、不完全なノードによるエラーを防止する |  |
| エッジ属性の値域制限 | 追加実装が必要 | /home/nixos/bin/src/kuzu/query/tests/sample/test_edge_attribute_constraints.ts | 関係の種類を標準化し、一貫性のある分析と可視化を可能にする |  |
| イミュータブルな履歴保証 | 追加実装が必要 | /home/nixos/bin/src/kuzu/query/tests/sample/test_immutable_history.ts | 過去のバージョン情報が改変されないことを保証し、監査証跡の信頼性を高める |  |
| メタデータの一貫性検証 | 追加実装が必要 | /home/nixos/bin/src/kuzu/query/tests/sample/test_metadata_consistency.ts | 属性値の一貫した使用を促進し、集計や分析の正確性を向上させる |  |

## 追加実装要件

以下の機能については、現在のDQLファイルに実装されていないため、追加実装が必要です：

1. **循環依存の検出と防止**
   - LocationURIのCONTAINS関係やRequirementEntityのDEPENDS_ON関係での循環参照を検出するクエリ
   - 循環検出時の警告または阻止メカニズム

2. **必須プロパティの検証**
   - 各ノード型の必須プロパティ（CodeEntity.persistent_id, RequirementEntity.id など）の存在を検証
   - 必須関係（すべてのCodeEntityはLocationURIに紐づくなど）の検証

3. **エッジ属性の値域制限**
   - implementation_type, dependency_type などの属性値が定義された選択肢内に収まるか検証
   - エッジの種類ごとに必須属性を検証

4. **イミュータブルな履歴保証**
   - 過去のVersionStateノードと関連エンティティの変更禁止を保証
   - バージョン間の時系列整合性を検証

5. **メタデータの一貫性検証**
   - 同種のノード間でのメタデータ使用の一貫性を検証
   - fragment や reference などの内部リンクの有効性を検証

これらの追加実装により、トレーサビリティモデルの信頼性と整合性が大幅に向上します。
