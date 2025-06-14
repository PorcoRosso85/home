source env.sh
source ./doc/shell/env.gcloud.sh

export LOG_EXECUTION_ID=false
# export FUNCTION_STAGING=https://asia-northeast1-bsp-pb-support-ai-stg.cloudfunctions.net/stg-pb-support-gcf-backend
# export CLOUDFUNCTION_RESOURCE_ID=stg-pb-support-gcf-backend
alias gcloud477='/root/genai-pb-support-backend/google-cloud-sdk/bin/gcloud'

# psql -h 35.200.102.109 -p 5432 -d pb_customer_service_manage -U pbadmin 
# $ pg-schema-diff plan --dsn "postgres://postgres:postgres@localhost:5432/postgres" --schema-dir ./schema
# <ホスト名>:<ポート番号>:<データベース名>:<ユーザー名>:<パスワード>
export DB_PUBLIC_IP=35.200.102.109
# pg-schema-diff plan --dsn postgres://pbadmin:ka9fU4{HU}~58VO@35.200.102.109:5432/pb_customer_service_manage --schema-dir ./schema
# pg-schema-diff plan --dsn postgres://$DB_USER:$DB_PASSWORD@$DB_PUBLIC_IP:5432/$DB_NAME --schema-dir ./db/schema
# %7BHU%7D~58VO
export DATABASE_URL="postgres://$DB_USER:ka9fU4%7BHU%7D~58VO@$DB_PUBLIC_IP:5432/$DB_NAME"


# echo "PYTHONPATH $PYTHONPATH"
# export PYTHONPATH="/home/nixos/charaview/.venv/bin/python"

echo "PYTHONDONTWRITEBYTECODE$PYTHONDONTWRITEBYTECODE"
export PYTHONDONTWRITEBYTECODE=1

export DEBUG=true
export AZURE_BING_API_KEY="a3036ebd1dd74c2dbbafc680201502e0"
echo "AZURE_BING_API_KEY $AZURE_BING_API_KEY"
export AZURE_BING_SEARCH_URL="https://api.bing.microsoft.com/v7.0/"
echo "AZURE_BING_SEARCH_URL $AZURE_BING_SEARCH_URL"

