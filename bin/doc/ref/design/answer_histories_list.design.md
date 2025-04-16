# 回答履歴一覧取得

- getAnswerHistoriesList
- FN0002

## 処理フロー

- APIエンドポイント GET /api/answer_histories_list
- Content-Type application/json

## パラメータ・リクエストボディ

- query string 問い合わせ文字列
- categories string カテゴリ（カンマ区切り）
- keyOrderBy string ソートキー（id, category, query, created_at）
- valueOrderBy string ソート順（0: 降順, 1: 昇順）
- pageSize string 1ページあたりの件数
- pageNumber string ページ番号

## 処理

- パラメータ取得とバリデーション  
  - 引数  
    - request CloudFunctionのリクエスト情報
  - 異常終了  
    - 400 必須パラメータ不足/入力値不正 ValidationError ログ出力

- 回答履歴一覧を取得する  
  - ページネーション機能を提供し、ページサイズに応じてレスポンスのデータを分割する
  - 引数  
    - データベースクライアント
    - バリデーションされたリクエスト情報 ページネーション条件
  - 異常終了  
    - 500 Internal server Errorレスポンス, CloudSQLErrorログ

- 回答履歴一覧をレスポンスする
  - 引数
    - 回答履歴
  - 正常終了  
    - 200 回答履歴一覧をレスポンス
