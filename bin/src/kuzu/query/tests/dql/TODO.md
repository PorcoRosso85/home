# 階層型トレーサビリティモデルの機能とファイルパス対応表

| 機能 | DQL ファイルパス | テスト実装用 TS ファイル | この機能追加で達成できる目的 | 完了 |
|------|------------|------------|------------|------|
| 循環依存の検出と防止 | 追加実装が必要 | /home/nixos/bin/src/kuzu/query/tests/sample/test_circular_dependency.ts | 循環参照による設計の複雑化やデッドロックを防止し、システムの安定性を高める |  |
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
