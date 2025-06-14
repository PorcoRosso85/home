gcloud config get-value compute/region
gcloud config get-value compute/zone

export $SERVICE_ACCOUNT_NAME
gcloud iam service-accounts create SERVICE_ACCOUNT_NAME \
    --display-name="SERVICE_ACCOUNT_DISPLAY_NAME"

gcloud auth print-access-token
# ya29.a0ARW5m77ufZdu8g1h_1wOzLvd67VfPZwoaNE_aR2Xnnoqh5JJi4gCN-cca9MVfECULN8cCb5H5OPcUvUz5Z2tipxSNquEZ9NH7YspKvoe0IG_VLFXJaJSyqf-NvoZD4QrHEv9DOlBJNg7LwqegDtc-vp-3tRLYwjN_QJqvPkzY9cV6waCgYKAfASARISFQHGX2MiMoOVLzov0kZDp36Sx4vcDw0181

# サービスアカウントキーを作成
gcloud iam service-accounts keys create $GOOGLE_APPLICATION_CREDENTIALS \
  --iam-account=$SERVICE_ACCOUNT_EMAIL

# 割り当て状況を確認
gcloud compute project-info describe --project=$PROJECT_ID
gcloud service-usage quotas list \
    --service=aiplatform.googleapis.com \
    --project=$PROJECT_ID

# SAのIAM確認
# gcloud projects get-iam-policy bsp-chatbn-test    --flatten="bindings[].members"    --format='table(bindings.role)'    --filter="bindings.members:chatbot@bsp-chatbn-test.iam.gserviceaccount.com"
gcloud projects get-iam-policy $PROJECT_ID --flatten="bindings[].members" --format='table(bindings.role)' --filter="bindings.members:$SERVICE_ACCOUNT_EMAIL"
