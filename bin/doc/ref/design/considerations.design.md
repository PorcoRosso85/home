# 考慮事項取得

- getConsiderations
- FN0006

## 処理フロー

- APIエンドポイント GET /api/considerations
- Content-Type application/json

## パラメータ・リクエストボディ

- outputFormat string 出力形式
- category string カテゴリ
- query string 考慮事項のクエリ

## 処理

- パラメータ取得とバリデーション  
  - 引数  
    - request CloudFunctionのリクエスト情報
  - 異常終了  
    - 400 必須パラメータ不足/入力値不正 ValidationError ログ出力

- CloudSQLクエリの実行  
  - 引数  
    - データベースクライアント
    - バリデーションされたリクエスト情報 検索条件
  - 異常終了  
    - 500 Internal server Errorレスポンス, CloudSQLErrorログ

- 正常終了  
  - 200 考慮事項をレスポンス
