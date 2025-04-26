# TODO: リファクタリングと機能追加

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