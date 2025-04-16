---

#### APIエンドポイントの処理  
Cloud Functionで受け取ったリクエストを処理する  
引数  
request (Request): HTTPリクエスト情報  
  
  

環境変数  

  



異常終了  
NotFoundErrorをログ  
ValidationErrorをログ  

  
#### AIコメント生成処理  
関連記事データを元にAIコメントを作成し生成結果を処理する  
引数  
ip_id (str): IP ID  
ip_name (str): IP名  
aggregate_dt (str): 集計日 (YYYY-MM-DD形式)  
  
環境変数  
RETRY_COUNT: AIコメント生成処理のリトライ回数  
GEMINI_MODEL_ID: モデルID  
GEMINI_TEMPERATURE: モデル温度
WEB_SITE_SEARCH_DAYS_BEFORE: 検索期間（開始日）  
WEB_SITE_SEARCH_DAYS_AFTER: 検索期間（終了日）  
異常終了  
SearchErrorをログ  
VertexAiErrorをログ  
  

  
#### AIコメント要約処理  
複数のAIコメントを結合して1つの要約を作成する  
引数  
comments (list): コメントリスト  
  
  

環境変数  
RETRY_COUNT: AIコメント生成処理のリトライ回数  
GEMINI_MODEL_ID: モデルID  
GEMINI_TEMPERATURE: モデル温度
GEMINI_MAX_OUTPUT_TOKENS: モデル生成出力の最大トークン数
GEMINI_TOPP: 出力の多様性を制御
  
異常終了  
VertexAiErrorをログ  
  

  
#### 再生成結果の格納処理  
再生成したAIコメントをクラウドストレージに保存する  
引数  
comment_data (Analyzed): コメントデータ  
  
  

環境変数  
CLOUD_STORAGE_BUCKET_NAME: クラウドストレージバケット名
CLOUD_STORAGE_PARQUET_FILE_NAME: 保存ファイル名

  

異常終了  
StorageErrorをログ  
