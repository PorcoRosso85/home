#### AIコメント作成対象IP取得処理
AIコメント作成対象のIPをBigQueryから取得する
指定された集計日の前日と当日のデータに基づきAIコメント作成対象のIPを特定する
引数
aggregate_dt (str): 集計日 (YYYY-MM-DD形式)
aggregate_dt_yesterday (str): 前日の集計日 (YYYY-MM-DD形式)


環境変数
PROJECT_ID: GCPのプロジェクトID
PROJECT_REGION: GCPのリージョン
BIGQUERY_DATASET: BigQueryのデータセット
BIGQUERY_TABLE_ID: BigQueryのテーブルID

異常終了
BigQueryErrorをログ


#### フィルタリング処理
BigQueryから取得したIPをフィルタリングする
SQL側で実施すると複雑になるフィルタリングをpandas DataFrameに適用し対象IPを絞り込む
引数




環境変数





異常終了



#### AIコメント作成処理
条件を満たしたIPに対してAIコメントを作成する
抽出されたIPアドレスに対してAIコメントを生成し、生成されたコメントを所定の場所に保存する
引数
ip_id (str): IP ID
ip_name (str): IP名
aggregate_date (str): 集計日 (YYYY-MM-DD形式)

環境変数
RETRY_COUNT: AIコメント生成処理のリトライ回数
GEMINI_MODEL_ID: GeminiのモデルID
GEMINI_TEMPERATURE: Geminiのモデル温度
WEB_SITE_SEARCH_DAYS_BEFORE: 検索期間(開始日)
WEB_SITE_SEARCH_DAYS_AFTER: 検索期間(終了日)
異常終了
SearchErrorをログ
VertexAiErrorをログ


#### 分析結果保存処理
AIコメントの分析結果を保存する
生成されたAIコメントと関連情報をParquet形式でクラウドストレージに保存する
引数
ai_comments (list[Analyzed]): AIコメントのリスト



環境変数
CLOUD_STORAGE_BUCKET_NAME: クラウドストレージバケット名
CLOUD_STORAGE_PARQUET_FILE_NAME: Parquetファイル名



異常終了
StorageErrorをログ



#### バッチ完了通知処理
バッチ処理の完了を通知する
バッチ処理が正常に完了したことを関係者に通知する
引数




環境変数
NOTIFICATION_URL: 通知URL
NOTIFICATION_MENTION_MEMBERS: 通知先メンバー



異常終了



#### 異常終了処理
バッチ処理が異常終了した場合の処理
エラー発生時に関係者への通知とエラーログの記録を行う
引数




環境変数
NOTIFICATION_URL: 通知URL
NOTIFICATION_MENTION_MEMBERS: 通知先メンバー



異常終了
UnexpectedError含むすべてのエラー型を状況に応じてログ