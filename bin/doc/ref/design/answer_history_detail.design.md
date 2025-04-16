# 回答履歴詳細取得

- getAnswerHistoryDetail
- FN0003

## 処理フロー

- APIエンドポイント GET /api/answer_history_detail
- Content-Type application/json

## パラメータ・リクエストボディ

- answerHistoryId string 回答履歴ID

## 処理

- パラメータ取得とバリデーション  
  - 引数  
    - request CloudFunctionのリクエスト情報
  - 異常終了  
    - 400 必須パラメータ不足/入力値不正 ValidationError ログ出力

- 指定したIDの回答履歴を取得する  
  - 引数  
    - データベースクライアント
    - バリデーションされたリクエスト情報 検索条件
  - 異常終了  
    - 400 該当のanswerHistoryIdが見つかりません。 ログ出力
    - 500 複数のanswerHistoryIdが見つかりました。 ログ出力
    - 500 Internal server Errorレスポンス, CloudSQLErrorログ

- 回答履歴をレスポンスする
  - 引数
    - 回答履歴
  - 正常終了  
    - 200 回答履歴をレスポンス
