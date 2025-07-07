# 削除候補テスト一覧 - kuzu/

## 削除基準
- 実装の詳細に密結合しているテスト
- ビジネス価値を検証していないテスト
- リファクタリングの障害となるテスト
- モックのみで実際の動作を保証しないテスト
- 存在/非存在の確認のみのテスト

## sync/src/syncClient.test.ts
- `should create a sync client instance` - インスタンス作成確認のみ、サーバー依存でスキップ
- `should demonstrate node creation API` - APIの存在確認のみ、実際の動作検証なし

## sync/src/phase2.test.ts
- `beforeEach`のモックセットアップ - モックが実装詳細に密結合
- モックサーバーの詳細実装がテスト内に含まれる

## sync/src/phase1.test.ts
- `should create and load snapshots from patch history` - existsSyncでファイル存在確認のみ
- `should handle empty patch history` - サイズが0より大きいことだけを確認

## sync/src/exportService.test.ts
- `KuzuDB Export - Parquet format` - existsSyncでファイル存在確認のみ

## browse/test/e2e/cases/basic.test.ts
- `E2E: UI初期表示` - TODOコメント、実装なし
- `E2E: グラフDB接続状態表示` - TODOコメント、実装なし
- `E2E: RPC接続状態表示` - TODOコメント、実装なし

## query/infrastructure/repositories/denoQueryRepository/uriValidation.test.ts
- URI検証テスト全般 - 正規表現マッチングのみでビジネスロジック検証が薄い