# 回答履歴情報取得

- getAnswerHistoryInfo
- FN0008

## 処理フロー

- リクエストにあたり、回答履歴保存テーブルに情報が記録されている
- APIエンドポイント GET /api/answer_history_info
- Content-Type application/json

## パラメータ・リクエストボディ

- categories string カテゴリのリスト（カンマ区切り）
- query string 回答履歴のクエリ
- pageSize string 1ページあたりの回答履歴数

## 処理

- パラメータ取得とバリデーション  
  - 引数  
    - request CloudFunctionのリクエスト情報
  - 異常終了  
    - 400 必須パラメータ不足/入力値不正 ValidationError ログ出力

- 指定したクエリとカテゴリで回答履歴を取得  
  - 引数  
    - データベースクライアント
    - バリデーションされたリクエスト情報
  - 異常終了  
    - 500 Internal server Errorレスポンス, CloudSQLErrorログ

- 回答履歴情報をレスポンスする
  - 正常終了  
    - 200 回答履歴情報をレスポンス
