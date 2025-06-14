# 選択可能な項目取得

- getSelectables
- FN0002

## 処理フロー

- APIエンドポイント GET /api/selectables
- Content-Type application/json

## パラメータ・リクエストボディ

- なし

## 処理

- 選択可能項目を取得する  
  - 引数  
    - データベースクライアント
  - 異常終了  
    - 500 Internal server Errorレスポンス, CloudSQLErrorログ

- 正常終了  
  - 200 セレクト可能な出力形式とカテゴリをレスポンス
