# レビュー登録

- postReview
- FN0004

## 処理フロー

- APIエンドポイント POST /api/review
- Content-Type application/json

## パラメータ・リクエストボディ

- answerHistoryId integer 回答履歴ID
- reviewBool boolean レビュー結果

## 処理

- パラメータ取得とバリデーション  
  - 引数  
    - request CloudFunctionのリクエスト情報
  - 異常終了  
    - 400 必須パラメータ不足/入力値不正 ValidationError ログ出力

- 評価情報を更新する  
  - 引数  
    - データベースクライアント
    - バリデーションされたリクエスト情報 検索条件
  - 異常終了  
    - 400 該当のanswerHistoryIdが見つかりません。 ログ出力
    - 500 複数のanswerHistoryIdが見つかりました。 ログ出力
    - 500 Internal server Errorレスポンス, CloudSQLErrorログ
