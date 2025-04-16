gcloud compute backend-services describe pb-support-ai --global --format="json"
# IAPは有効になっている

gcloud iap oauth-brands list
# gcloud iap oauth-brands describe --project=$PROJECT_ID
echo $PROJECT_NUMBER && gcloud iap oauth-brands describe projects/$PROJECT_NUMBER/brands/$PROJECT_NUMBER

# permission denied
echo $PROJECT_NUMBER && gcloud iap oauth-clients list projects/$PROJECT_NUMBER/brands/$PROJECT_NUMBER
