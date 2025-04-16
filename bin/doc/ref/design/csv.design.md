# CSVエクスポート

- getCSV
- FN0005

## 処理フロー

- APIエンドポイント GET /api/csv
- Media-Type text/csv

## パラメータ・リクエストボディ

- answerHistoryId string 回答履歴IDのリスト（カンマ区切り）

## 処理

- パラメータ取得とバリデーション  
  - 引数  
    - request CloudFunctionのリクエスト情報
  - 異常終了  
    - 400 必須パラメータ不足/入力値不正 ValidationError ログ出力

- クエリを実行して結果をCSVファイルに格納  
  - 引数  
    - データベースクライアント
    - バリデーションされたリクエスト情報 検索条件(複数のanswerHistoryIdを指定可能)
  - 異常終了  
    - 400 該当のanswerHistoryIdが見つかりません。 ログ出力(存在しないanswerHistoryIdが指定された場合)
    - 500 Internal server Errorレスポンス, CloudSQLErrorログ

- CSVファイルをレスポンスする
  - 引数
    - CSVファイル
  - 正常終了  
    - 200 CSVファイルをレスポンス, ログ出力
