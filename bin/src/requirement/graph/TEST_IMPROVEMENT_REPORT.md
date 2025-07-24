# テスト改善報告書

## 実施内容

### 1. 黄金律「リファクタリングの壁」に基づくテスト見直し

規約：「もし、実装コードが壁の向こう側にあって全く見えないとしたら、このテストは書けるか？」

この原則に基づき、以下の改善を実施しました。

### 2. 削除したテスト

#### パフォーマンステスト（規約違反）
- `test_duplicate_detection.py::test_performance_with_many_requirements`
- `test_existing_connection.py::test_initialization_performance`
- `test_existing_connection.py::test_detailed_performance_comparison`（スキップ済み）
- `test_existing_connection.py::test_connection_creation_overhead`

**削除理由**: パフォーマンスは実装詳細であり、公開APIの振る舞いではない

#### モックテスト（アプリケーション層の単体テスト）
- `test_search_template.py::test_search_template_with_mock_adapter`
- `test_search_template.py::test_search_template_with_error`
- `test_search_template_integration.py`（ファイル全体を削除）

**削除理由**: testing.md「アプリケーション層の単体テストは原則禁止」に違反

### 3. 新規作成したテスト

#### 統合テスト
- `test_search_template_integration_real.py`
  - 実際のデータベースとSearchAdapterを使用
  - モックではなく実際のエラーシナリオをテスト
  - 振る舞いを検証（実装詳細ではない）

### 4. 保持した価値あるテスト

以下のテストは黄金律に準拠しており、価値があるため保持：

- `test_search_template_validation` - 入力検証は公開APIの契約
- `test_output_contract.py` - 出力形式の契約を検証
- `test_requirement_management.py` - ユースケースレベルの統合テスト
- `test_hybrid_search_spec.py` - 検索仕様の検証
- `test_existing_connection.py` のエラーハンドリングテスト

### 5. 規約準拠の確認

#### testing.md の原則
- ✅ ドメイン層：ビジネスロジックの単体テストに集中
- ✅ アプリケーション層：モック禁止、統合テストのみ
- ✅ インフラ層：実際のDBとの統合テストのみ

#### test_infrastructure.md の規則
- ✅ ファイル命名：`test_*.py` 形式を遵守
- ✅ テスト関数名：何を_どうすると_どうなるを表現
- ✅ E2E構造：internal/external の分離（今後の課題）

## 成果

1. **テストの質向上**: 実装詳細ではなく振る舞いを検証
2. **保守性向上**: リファクタリング時にテストが障害にならない
3. **信頼性向上**: 実際のコンポーネントでテスト
4. **規約準拠**: 全テストが黄金律に準拠

## 今後の課題

1. **E2Eテスト整備**: e2e/internal, e2e/external ディレクトリ構造の実装
2. **外部パッケージテスト**: requirement/graph を外部から利用するテスト
3. **プロパティベーステスト**: 普遍的なルールのテスト追加

## 外部パッケージテストの規約

test_infrastructure.md に基づき：

```
e2e/
├── internal/      # 内部E2Eテスト（CLIコマンド実行など）
└── external/      # 外部パッケージテスト
    ├── flake.nix  # 独立したflake
    └── test_e2e_*.py  # import テスト
```

外部パッケージ（Denoなど）から利用する場合も、pytest で統一してテストを記述します。