# Cloud Functions をデプロイ
gcloud functions deploy $CLOUD_FUNCTION_NAME \
--runtime python311 \
--trigger-http \
--region $PROJECT_REGION\
--source src.function
