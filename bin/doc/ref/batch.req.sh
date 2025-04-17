# cd batch # batch ディレクトリに移動
gcloud run deploy batch-service \ # サービス名 (任意)
    --source . \              # ソースコードの場所 (現在のディレクトリ)
    --region <リージョン> \      # デプロイするリージョン (例: us-central1, asia-northeast1)
    --platform managed        # マネージド環境を使用
    
curl -X GET https://localhost:8080/analyze

curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" https://stg-bsp-chatbn-test-gcr-1066839057921.asia-northeast1.run.app/analyze

curl -X POST http://localhost:8080/analyze \
-H "Content-Type: application/json" \
-d '{
    "job_name": "test_job",
    "status": "error",
    "mention_members": ["tetsuya.takasawa@zdh.co.jp", ""],
    "error_message": "test_job実行時にエラー発生"
}'
