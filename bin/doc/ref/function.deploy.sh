gcloud functions deploy function-name \      # 関数名 (任意)
    --runtime python311 \                  # ランタイム (例: python37, python39, python310)
    --trigger-http \                     # HTTP トリガーを使用する場合
    --region <リージョン> \               # デプロイするリージョン
    --source .                            # ソースコードの場所 (現在のディレクトリ)