# 問い合わせ回答取得保存

- postQueryAndSave
- FN0001

## 処理フロー

- APIエンドポイント POST /api/query_and_save
- Media-Type text/event-stream

## パラメータ・リクエストボディ

- outputFormat string 出力形式
- consideration string 回答生成時の考慮事項
- category string カテゴリ
- query string 問い合わせ内容
- userEmail string ユーザーメールアドレス (Optional)
- modelID string (optional) 使用するモデルID

## 処理

- パラメータ取得とバリデーション  
  - 引数  
    - request CloudFunctionのリクエスト情報
  - 異常終了  
    - 400 必須パラメータ不足/入力値不正/リクエストボディが大きすぎる ValidationError ログ出力

- 個人情報チェック  
  - 引数  
    - バリデーションされたリクエスト情報
  - 環境変数  
    - FAST_MODEL_ID 高速モデルID
  - 異常終了
    - 200 個人情報が含まれている場合のレスポンス (PersonalInfoError) ログ出力
    - 500 Internal Server Errorレスポンス, CloudSqlError または VertexAIError ログ出力
    - 429 Too Many Requestsレスポンス (VertexAIErrorの場合のみ)

- 参考ドキュメントの検索  
  - 引数  
    - 構築されたプロンプト
    - ページサイズ
  - 環境変数  
    - SEARCH_AGENT_PAGE_SIZE ページサイズ
  - 異常終了  
    - 500 Internal server Errorレスポンス, AgentBuilderError ログ出力

- 回答の生成とストリーミングレスポンス  
  - 回答はストリーミング形式  
  - VertexAIのモデルないしAnthropic Claudeのモデルによる回答生成、パラメータおよび環境変数によるモデル選択可能
  - 環境変数  
    - DEFAULT_MODEL_ID デフォルトの出力モデルID
    - CLAUDE35_MODEL_ID Anthropic ClaudeモデルID
  - 引数  
    - modelID パラメータまたは環境変数によるモデル選択
    - バリデーションされたリクエスト情報
    - 構築されたプロンプト
    - 参考ドキュメント
  - 異常終了  
    - 500 Internal server Errorレスポンス, VertexAIError ログ出力

- 過去案件履歴の検索  
  - 引数  
    - searchServiceClient ユーザー入力をもとに過去案件履歴を取得
    - バリデーションされたリクエスト情報
  - 異常終了  
    - 500 Internal server Errorレスポンス, AgentBuilderError ログ出力

- 回答履歴の保存  
  - 引数  
    - sqlClient データベースクライアント
    - 格納する回答履歴
  - 環境変数
    - HISTORY_TABLE_NAME 回答履歴を保存するCloud SQLのテーブル名
  - 異常終了  
    - 500 Internal server Errorレスポンス, DatabaseError ログ出力

- レスポンスの終了処理
  - 回答情報テール(templateId, caseHistoryId, answerHistoryId)のストリーミングレスポンス
  - レスポンスエンドのストリーミングレスポンス
  - 正常終了
    - 200 ログ出力

## 後処理

- 後処理は処理の最後に必ず実行される (レスポンス終了時ないしfinally到達時)
- 終了時のログ出力
- 接続終了処理

## 環境変数

- `CLOUD_LOGGING_LOG_NAME` Cloud Loggingのログ名
- `PROJECT_ID` Google CloudのプロジェクトID
- `HISTORY_TABLE_NAME` 回答履歴を保存するCloud SQLのテーブル名
- `SEARCH_AGENT_PAGE_SIZE` 検索エージェントのページサイズ
- `CHECKLIST_FORMAT_STR` チェックリスト形式の出力形式
- `FAST_MODEL_ID` 高速モデルID
- `DEFAULT_MODEL_ID` デフォルトの出力モデルID
- `CLAUDE35_MODEL_ID` Anthropic ClaudeモデルID
