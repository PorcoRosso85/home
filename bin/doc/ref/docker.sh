# Dockerfileがあるディレクトリで実行
# docker build -t <地域>-docker.pkg.dev/<プロジェクトID>/<リポジトリ名>/<イメージ名>:<タグ> .
# docker push <地域>-docker.pkg.dev/<プロジェクトID>/<リポジトリ名>/<イメージ名>:<タグ>

sudo docker build -t $PROJECT_REGION-docker.pkg.dev/$PROJECT_ID/$CONTAINER_REPOSITORY_NAME/$CONTAINER_IMAGE_NAME:$CONTAINER_IMAGE_TAG .

sudo docker run --rm asia-northeast1-docker.pkg.dev/bsp-chatbn-test/charaview/charaview_batch:latest
sudo docker run --rm -t $PROJECT_REGION-docker.pkg.dev/$PROJECT_ID/$CONTAINER_REPOSITORY_NAME/$CONTAINER_IMAGE_NAME:$CONTAINER_IMAGE_TAG
