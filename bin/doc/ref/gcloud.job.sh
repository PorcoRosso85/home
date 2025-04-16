gcloud run jobs create "${CONTAINER_JOB_NAME}" \
  --image "${PROJECT_REGION}-docker.pkg.dev/${PROJECT_ID}/${CONTAINER_REPOSITORY_NAME}/${CONTAINER_IMAGE_NAME}:${CONTAINER_IMAGE_TAG}" \
  --region="${PROJECT_REGION}" \
  --tasks=1 \
  --cpu=1 \
  --max-retries=0 \
  --memory=512Mi \
  --parallelism=1 \
  --task-timeout=100 \


gcloud run jobs execute $CONTAINER_JOB_NAME --region=${PROJECT_REGION}
