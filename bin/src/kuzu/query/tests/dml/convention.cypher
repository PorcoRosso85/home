// 階層型トレーサビリティモデル - CONVENTION規約用DML
// CONVENTION.yamlを削除しても利用可能な規約格納スクリプト

// ===== 規約階層のLocationURIノード作成 =====

// ルートノード作成
CREATE (root:LocationURI {
  uri_id: 'convention:root',
  scheme: 'convention',
  authority: 'internal',
  path: '/CONVENTION',
  fragment: '',
  query: NULL
});

// 基本原則カテゴリ
CREATE (cat_basic:LocationURI {
  uri_id: 'convention:基本原則',
  scheme: 'convention',
  authority: 'internal',
  path: '/CONVENTION',
  fragment: '基本原則',
  query: NULL
});

// 型定義カテゴリ
CREATE (cat_types:LocationURI {
  uri_id: 'convention:基本原則.型定義',
  scheme: 'convention',
  authority: 'internal',
  path: '/CONVENTION',
  fragment: '基本原則.型定義',
  query: NULL
});

// エラー処理カテゴリ
CREATE (cat_error:LocationURI {
  uri_id: 'convention:基本原則.エラー処理',
  scheme: 'convention',
  authority: 'internal',
  path: '/CONVENTION',
  fragment: '基本原則.エラー処理',
  query: NULL
});

// 禁止事項カテゴリ
CREATE (cat_prohibited:LocationURI {
  uri_id: 'convention:禁止事項',
  scheme: 'convention',
  authority: 'internal',
  path: '/CONVENTION',
  fragment: '禁止事項',
  query: NULL
});

// 推奨事項カテゴリ
CREATE (cat_recommended:LocationURI {
  uri_id: 'convention:推奨される実装スタイル',
  scheme: 'convention',
  authority: 'internal',
  path: '/CONVENTION',
  fragment: '推奨される実装スタイル',
  query: NULL
});

// ファイル構造カテゴリ
CREATE (cat_file:LocationURI {
  uri_id: 'convention:ファイル構造とモジュール設計',
  scheme: 'convention',
  authority: 'internal',
  path: '/CONVENTION',
  fragment: 'ファイル構造とモジュール設計',
  query: NULL
});

// テストカテゴリ
CREATE (cat_test:LocationURI {
  uri_id: 'convention:テスト',
  scheme: 'convention',
  authority: 'internal',
  path: '/CONVENTION',
  fragment: 'テスト',
  query: NULL
});

// 具体的なルールノード
CREATE (rule_typeddict:LocationURI {
  uri_id: 'convention:基本原則.型定義.TypedDict',
  scheme: 'convention',
  authority: 'internal',
  path: '/CONVENTION',
  fragment: '基本原則.型定義.TypedDict',
  query: NULL
});

CREATE (rule_error_handling:LocationURI {
  uri_id: 'convention:基本原則.エラー処理.戻り値エラー型',
  scheme: 'convention',
  authority: 'internal',
  path: '/CONVENTION',
  fragment: '基本原則.エラー処理.戻り値エラー型',
  query: NULL
});

CREATE (rule_no_class:LocationURI {
  uri_id: 'convention:禁止事項.クラス',
  scheme: 'convention',
  authority: 'internal',
  path: '/CONVENTION',
  fragment: '禁止事項.クラス',
  query: NULL
});

CREATE (rule_no_exception:LocationURI {
  uri_id: 'convention:禁止事項.例外',
  scheme: 'convention',
  authority: 'internal',
  path: '/CONVENTION',
  fragment: '禁止事項.例外',
  query: NULL
});

CREATE (rule_pure_func:LocationURI {
  uri_id: 'convention:推奨される実装スタイル.関数のみで実装',
  scheme: 'convention',
  authority: 'internal',
  path: '/CONVENTION',
  fragment: '推奨される実装スタイル.関数のみで実装',
  query: NULL
});

CREATE (rule_immutability:LocationURI {
  uri_id: 'convention:推奨される実装スタイル.不変性の確保',
  scheme: 'convention',
  authority: 'internal',
  path: '/CONVENTION',
  fragment: '推奨される実装スタイル.不変性の確保',
  query: NULL
});

CREATE (rule_unittest:LocationURI {
  uri_id: 'convention:テスト.単体テスト',
  scheme: 'convention',
  authority: 'internal',
  path: '/CONVENTION',
  fragment: 'テスト.単体テスト',
  query: NULL
});

// ===== 階層関係の構築 =====

// ルートと主要カテゴリの関係
MATCH (root:LocationURI {uri_id: 'convention:root'}),
      (cat_basic:LocationURI {uri_id: 'convention:基本原則'})
CREATE (root)-[:CONTAINS_LOCATION {relation_type: 'hierarchy'}]->(cat_basic);

MATCH (root:LocationURI {uri_id: 'convention:root'}),
      (cat_prohibited:LocationURI {uri_id: 'convention:禁止事項'})
CREATE (root)-[:CONTAINS_LOCATION {relation_type: 'hierarchy'}]->(cat_prohibited);

MATCH (root:LocationURI {uri_id: 'convention:root'}),
      (cat_recommended:LocationURI {uri_id: 'convention:推奨される実装スタイル'})
CREATE (root)-[:CONTAINS_LOCATION {relation_type: 'hierarchy'}]->(cat_recommended);

MATCH (root:LocationURI {uri_id: 'convention:root'}),
      (cat_file:LocationURI {uri_id: 'convention:ファイル構造とモジュール設計'})
CREATE (root)-[:CONTAINS_LOCATION {relation_type: 'hierarchy'}]->(cat_file);

MATCH (root:LocationURI {uri_id: 'convention:root'}),
      (cat_test:LocationURI {uri_id: 'convention:テスト'})
CREATE (root)-[:CONTAINS_LOCATION {relation_type: 'hierarchy'}]->(cat_test);

// 基本原則下の階層関係
MATCH (cat_basic:LocationURI {uri_id: 'convention:基本原則'}),
      (cat_types:LocationURI {uri_id: 'convention:基本原則.型定義'})
CREATE (cat_basic)-[:CONTAINS_LOCATION {relation_type: 'hierarchy'}]->(cat_types);

MATCH (cat_basic:LocationURI {uri_id: 'convention:基本原則'}),
      (cat_error:LocationURI {uri_id: 'convention:基本原則.エラー処理'})
CREATE (cat_basic)-[:CONTAINS_LOCATION {relation_type: 'hierarchy'}]->(cat_error);

// 型定義下のルール
MATCH (cat_types:LocationURI {uri_id: 'convention:基本原則.型定義'}),
      (rule_typeddict:LocationURI {uri_id: 'convention:基本原則.型定義.TypedDict'})
CREATE (cat_types)-[:CONTAINS_LOCATION {relation_type: 'hierarchy'}]->(rule_typeddict);

// エラー処理下のルール
MATCH (cat_error:LocationURI {uri_id: 'convention:基本原則.エラー処理'}),
      (rule_error_handling:LocationURI {uri_id: 'convention:基本原則.エラー処理.戻り値エラー型'})
CREATE (cat_error)-[:CONTAINS_LOCATION {relation_type: 'hierarchy'}]->(rule_error_handling);

// 禁止事項下のルール
MATCH (cat_prohibited:LocationURI {uri_id: 'convention:禁止事項'}),
      (rule_no_class:LocationURI {uri_id: 'convention:禁止事項.クラス'})
CREATE (cat_prohibited)-[:CONTAINS_LOCATION {relation_type: 'hierarchy'}]->(rule_no_class);

MATCH (cat_prohibited:LocationURI {uri_id: 'convention:禁止事項'}),
      (rule_no_exception:LocationURI {uri_id: 'convention:禁止事項.例外'})
CREATE (cat_prohibited)-[:CONTAINS_LOCATION {relation_type: 'hierarchy'}]->(rule_no_exception);

// 推奨事項下のルール
MATCH (cat_recommended:LocationURI {uri_id: 'convention:推奨される実装スタイル'}),
      (rule_pure_func:LocationURI {uri_id: 'convention:推奨される実装スタイル.関数のみで実装'})
CREATE (cat_recommended)-[:CONTAINS_LOCATION {relation_type: 'hierarchy'}]->(rule_pure_func);

MATCH (cat_recommended:LocationURI {uri_id: 'convention:推奨される実装スタイル'}),
      (rule_immutability:LocationURI {uri_id: 'convention:推奨される実装スタイル.不変性の確保'})
CREATE (cat_recommended)-[:CONTAINS_LOCATION {relation_type: 'hierarchy'}]->(rule_immutability);

// テスト下のルール
MATCH (cat_test:LocationURI {uri_id: 'convention:テスト'}),
      (rule_unittest:LocationURI {uri_id: 'convention:テスト.単体テスト'})
CREATE (cat_test)-[:CONTAINS_LOCATION {relation_type: 'hierarchy'}]->(rule_unittest);

// ===== ReferenceEntity の作成（具体的な規約内容） =====

// TypedDictルール
CREATE (ref_typeddict:ReferenceEntity {
  id: 'CONV_RULE_001',
  description: 'TypedDictを使用すること。各層のtypes.pyファイルに型定義を集約し、可能な限り型アノテーションを使用すること。',
  type: 'CONVENTION_RULE',
  source_type: 'internal'
});

// エラー処理ルール
CREATE (ref_error:ReferenceEntity {
  id: 'CONV_RULE_002',
  description: '例外を投げる代わりに、定義したエラー型を返却すること。関数の戻り値として成功/失敗を表現すること。',
  type: 'CONVENTION_RULE',
  source_type: 'internal'
});

// クラス禁止ルール
CREATE (ref_no_class:ReferenceEntity {
  id: 'CONV_RULE_003',
  description: 'classキーワードを使用したクラス定義は避けること。オブジェクト指向設計の代わりに、関数とデータの明確な分離を行う。',
  type: 'CONVENTION_RULE',
  source_type: 'internal'
});

// 例外禁止ルール
CREATE (ref_no_exception:ReferenceEntity {
  id: 'CONV_RULE_004',
  description: 'try/exceptブロックや例外の使用は避けること。明示的なエラー型とエラーハンドリング関数を使用する。',
  type: 'CONVENTION_RULE',
  source_type: 'internal'
});

// 純粋関数推奨ルール
CREATE (ref_pure_func:ReferenceEntity {
  id: 'CONV_RULE_005',
  description: '可能な限り純粋関数を使用すること。同じ入力に対して常に同じ出力を返し、副作用のない関数を使用すること。',
  type: 'CONVENTION_RULE',
  source_type: 'internal'
});

// 不変性確保ルール
CREATE (ref_immutability:ReferenceEntity {
  id: 'CONV_RULE_006',
  description: 'データの変更は避け、新しいデータ構造を返すこと。リスト操作にはmap、filter、reduceなどの高階関数を使用すること。',
  type: 'CONVENTION_RULE',
  source_type: 'internal'
});

// 単体テストルール
CREATE (ref_unittest:ReferenceEntity {
  id: 'CONV_RULE_007',
  description: '単体テストは別途テストファイルは作成せず、実装ファイル内に記述すること。if __name__ == "__main__"ブロック内にテストケースを記述すること。',
  type: 'CONVENTION_RULE',
  source_type: 'internal'
});

// ===== ReferenceEntityとLocationURIの関連付け =====

// TypedDictルールの関連付け
MATCH (ref:ReferenceEntity {id: 'CONV_RULE_001'}),
      (loc:LocationURI {uri_id: 'convention:基本原則.型定義.TypedDict'})
CREATE (ref)-[:REFERENCE_HAS_LOCATION]->(loc);

// エラー処理ルールの関連付け
MATCH (ref:ReferenceEntity {id: 'CONV_RULE_002'}),
      (loc:LocationURI {uri_id: 'convention:基本原則.エラー処理.戻り値エラー型'})
CREATE (ref)-[:REFERENCE_HAS_LOCATION]->(loc);

// クラス禁止ルールの関連付け
MATCH (ref:ReferenceEntity {id: 'CONV_RULE_003'}),
      (loc:LocationURI {uri_id: 'convention:禁止事項.クラス'})
CREATE (ref)-[:REFERENCE_HAS_LOCATION]->(loc);

// 例外禁止ルールの関連付け
MATCH (ref:ReferenceEntity {id: 'CONV_RULE_004'}),
      (loc:LocationURI {uri_id: 'convention:禁止事項.例外'})
CREATE (ref)-[:REFERENCE_HAS_LOCATION]->(loc);

// 純粋関数推奨ルールの関連付け
MATCH (ref:ReferenceEntity {id: 'CONV_RULE_005'}),
      (loc:LocationURI {uri_id: 'convention:推奨される実装スタイル.関数のみで実装'})
CREATE (ref)-[:REFERENCE_HAS_LOCATION]->(loc);

// 不変性確保ルールの関連付け
MATCH (ref:ReferenceEntity {id: 'CONV_RULE_006'}),
      (loc:LocationURI {uri_id: 'convention:推奨される実装スタイル.不変性の確保'})
CREATE (ref)-[:REFERENCE_HAS_LOCATION]->(loc);

// 単体テストルールの関連付け
MATCH (ref:ReferenceEntity {id: 'CONV_RULE_007'}),
      (loc:LocationURI {uri_id: 'convention:テスト.単体テスト'})
CREATE (ref)-[:REFERENCE_HAS_LOCATION]->(loc);

// ===== バージョン管理との連携 =====

// 初期バージョンの作成
CREATE (v:VersionState {
  id: 'convention_v1.0.0',
  timestamp: '2025-05-07T12:00:00Z',
  commit_id: 'init_convention_graph',
  branch_name: 'main'
});