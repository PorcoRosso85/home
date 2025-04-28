# TODO: リファクタリングと機能追加

## UX向上のためのSHACL制約によるフィードバック改善

- [ ] クエリ実行コマンドの拡張
  - [ ] `/home/nixos/bin/src/kuzu/upsert/interface/cli.py` にクエリ実行コマンド（`--query`）を追加
    - [ ] 構文: `--query <cypher_query>` (例: `--query "MATCH (f:FunctionType) RETURN f.title LIMIT 5"`)
    - [ ] パラメータ対応: `--param name=value` のような追加オプションで、クエリ内の$nameパラメータに値を渡せるように実装
  - [ ] `--help-query` オプションの追加
    - [ ] 特定のクエリキーワードやコンテキストに応じたヘルプを表示
    - [ ] 構文: `--help-query <keyword>` (例: `--help-query "MATCH"`, `--help-query "CREATE"`)
    - [ ] 関連するSHACL制約の説明も含める
  - [ ] `--show-examples` オプションの追加
    - [ ] 指定されたタイプのサンプルクエリを表示
    - [ ] 構文: `--show-examples <type>` (例: `--show-examples "node"`, `--show-examples "relationship"`)
    - [ ] タイプ指定なしの場合は基本的なCRUDクエリ例をすべて表示
  - [ ] SHACLエラー表示の改善
    - [ ] エラーメッセージをカラーコード化（赤：エラー、黄：警告、緑：情報）
    - [ ] エラーの位置や種類を視覚的にわかりやすく表示
    - [ ] 解決策の提案を含める

- [ ] クエリサービスの実装
  - [ ] `/home/nixos/bin/src/kuzu/upsert/application/query_service.py` を新規作成し、クエリ実行とSHACL検証を統合
    - [ ] クエリからRDFデータに変換
    - [ ] SHACL制約に対して事前検証
    - [ ] 検証結果に基づくフィードバック生成
  - [ ] 検証パス後のクエリ実行機能の実装
    - [ ] 検証に成功した場合のみクエリを実行
    - [ ] 結果の整形と返却
    - [ ] 実行時エラーの詳細なフォーマット
  - [ ] トランザクション的なクエリ実行の実装
    - [ ] 複数のクエリを一連の操作として実行
    - [ ] 中間段階でのSHACL検証を含める
    - [ ] すべての操作が成功した場合のみコミット
  - [ ] クエリ結果のわかりやすい表示機能の実装
    - [ ] 表形式での結果表示
    - [ ] 統計情報の追加（実行時間、影響を受けた行数など）
    - [ ] 結果セットが大きい場合のページング対応

- [ ] バリデーション結果の強化
  - [ ] `/home/nixos/bin/src/kuzu/upsert/application/validation_service.py` にSHACLバリデーション結果の詳細なフォーマット機能を追加
    - [ ] エラーの種類ごとにグループ化と分類
    - [ ] エラーの重要度に基づく優先順位付け
    - [ ] 関連するデータモデルの要素への参照
  - [ ] 人間が理解しやすいエラーメッセージに変換する機能を実装
    - [ ] 技術的なSHACLエラーメッセージを自然言語に変換
    - [ ] コンテキストに応じた説明の追加
    - [ ] 修正例を含む改善提案
  - [ ] バリデーション結果の視覚的な表現の実装
    - [ ] エラー箇所のハイライト表示
    - [ ] グラフベースのエラー表示（ノードと関係の問題を視覚的に示す）
    - [ ] プログレスバーや成功率の表示
  - [ ] カスタマイズ可能なバリデーションレベルの実装
    - [ ] 厳格モード：すべてのSHACL制約を厳密に適用
    - [ ] 標準モード：重要な制約のみを適用
    - [ ] 警告モード：エラーは表示するが実行は許可

- [ ] エラー変換サービスの実装
  - [ ] `/home/nixos/bin/src/kuzu/upsert/domain/services/error_translator.py` を新規作成
    - [ ] エラーコードと種類に基づくメッセージマッピング
    - [ ] エラーの具体的な内容と原因の説明
    - [ ] ドメイン固有の用語の一般的な表現への変換
  - [ ] エラーの種類別に対処方法を提示する機能を実装
    - [ ] 一般的なエラーパターンに対する解決策の提案
    - [ ] 同様のエラーを回避するためのベストプラクティス
    - [ ] 特定のエラーに対する具体的な修正例
  - [ ] エラーメッセージのテンプレート管理の実装
    - [ ] 各エラー種類に対応するメッセージテンプレートの定義
    - [ ] コンテキスト変数を使用したメッセージのカスタマイズ
    - [ ] 多言語対応の基盤
  - [ ] エラーコンテキストの強化
    - [ ] エラーが発生した状況の詳細な情報の提供
    - [ ] 関連するデータモデルやSHACL制約への参照
    - [ ] 問題の影響範囲の説明

- [x] サンプルクエリの整備
  - [ ] `/home/nixos/bin/src/kuzu/query/examples/` ディレクトリを新規作成
  - [ ] 基本的なCRUD操作のサンプルクエリファイルを追加
    - [ ] ノード作成：`create_node.cypher`
    - [ ] ノード検索：`find_node.cypher`
    - [ ] ノード更新：`update_node.cypher`
    - [ ] ノード削除：`delete_node.cypher`
  - [ ] 関係操作のサンプルクエリを追加
    - [ ] 関係作成：`create_relationship.cypher`
    - [ ] 関係を持つノード検索：`find_related_nodes.cypher`
    - [ ] 関係プロパティ更新：`update_relationship.cypher`
    - [ ] 関係削除：`delete_relationship.cypher`
  - [ ] 複雑なクエリパターンの例を追加
    - [ ] 多段階の関係を持つノード検索：`find_multi_hop.cypher`
    - [ ] 集計関数を使った分析：`aggregation_query.cypher`
    - [ ] 条件付きパス探索：`conditional_path.cypher`
    - [ ] サブクエリの使用例：`subquery_example.cypher`
  - [ ] SHACLルールに準拠したデータ操作の例を追加
    - [ ] 制約を考慮したノード作成：`shacl_compliant_create.cypher`
    - [ ] プロパティ制約を満たす更新：`shacl_compliant_update.cypher`
    - [ ] 関係制約に準拠した操作：`shacl_compliant_relationship.cypher`
    - [ ] 複合制約を扱うクエリ：`complex_constraints.cypher`

- [ ] クエリヘルプサービスの実装
  - [ ] `/home/nixos/bin/src/kuzu/upsert/application/query_helper.py` を新規作成
    - [ ] Cypher構文の基本説明（MATCH, CREATE, WHERE, RETURNなど）
    - [ ] パラメータ使用法の説明
    - [ ] パターンマッチングの詳細な説明
    - [ ] クエリ最適化のヒント
  - [ ] クエリのコンテキストやキーワードに応じたヘルプを返す機能を実装
    - [ ] キーワード検索に基づく関連情報の提供
    - [ ] 部分的なクエリからの補完候補の提示
    - [ ] 同様のクエリパターンの提案
    - [ ] エラーが発生した際の代替クエリの提案
  - [ ] データモデル依存のヘルプ機能を実装
    - [ ] 現在のデータモデルに基づく有効な操作の表示
    - [ ] 使用可能なノードラベルとプロパティの一覧
    - [ ] 関係タイプとその制約の説明
    - [ ] 典型的なユースケースに基づくクエリパターン
  - [ ] 対話的なクエリビルダーのサポート機能を実装
    - [ ] クエリ部品の段階的な選択肢の提示
    - [ ] クエリの各部分に対する説明と選択肢
    - [ ] 現在のコンテキストで使用可能な次のステップの提案
    - [ ] SHACL制約を考慮したクエリ構築ガイダンス

## application層にある他層処理移行

- [ ] 責務外の現状確認
  - [ ] クエリもその一つ
  - [ ] アプリ定数、環境変数は1か所
- [ ] 責務通りへリファクタリング

## ノード構造の統一

- [x] 現状の実装: `Function`, `Parameter`, `ReturnType` の3つのノードタイプが存在
- [x] リファクタリング: すべてのノードを `xxxType` という命名規則に統一する
  - [x] `Function` → `FunctionType`
  - [x] `Parameter` → `ParameterType`
  - [x] `ReturnType` → そのまま（すでに`Type`が付いている）
- [ ] 統合: `Parameter` と `ReturnType` を `FunctionType` に統合する
  - 最終的に `FunctionType` ノードのみが残る構造にする

## 関数間の関係（エッジ）の実装

- [ ] 関数間の関係を表す新しいエッジタイプを定義する
  - [ ] `CALLS`: 関数Aが関数Bを呼び出す関係
  - [ ] `DEPENDS_ON`: 関数Aが関数Bに依存する関係
  - [ ] `COMPOSED_OF`: 関数Aが関数Bを内部で使用する合成関係

- [ ] 関数間エッジを作成するAPIを実装する
  ```python
  def create_function_relationship(
      conn: Any, 
      source_function: str, 
      target_function: str, 
      relationship_type: str
  ) -> RelationshipCreationResult:
      """2つの関数ノード間にエッジを作成する"""
      pass
  ```

- [ ] JSONからの関数関係インポート機能を追加する
  ```python
  def add_function_relationship_from_json(
      json_file: str
  ) -> Tuple[bool, str]:
      """JSONファイルから関数間の関係を追加する"""
      pass
  ```

## グラフクエリの拡張

- [ ] 関数の依存関係を検索するクエリを実装する
- [ ] 関数の呼び出し階層を取得するクエリを実装する
- [ ] 特定の関数に依存するすべての関数を検索するクエリを実装する

## データモデルの修正

- [ ] `domain/models/relationship.py` を更新して新しい関係タイプを追加する
- [ ] Kuzu用のCypherクエリテンプレートを更新する

