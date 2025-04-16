echo "./doc/shell/env.sh"
export LOG_EXECUTION_ID=true
export PROJECT_ID=bsp-chatbn-test
export PROJECT_REGION=asia-northeast1

# WARNING
export PROJECT_API_KEY=AIzaSyAaH6QLUEE4D-CjC8WGVM8pSAmlg_YrOuM

# https://developers.google.com/custom-search/v1/overview?hl=ja
# https://zenn.dev/eito_blog/articles/653d4d8bf20320
# https://programmablesearchengine.google.com/controlpanel/create
export CUSTOM_SEARCH_ENGINE_NAME=bsp-chatbn-test-searchengine
# <script async src="https://cse.google.com/cse.js?cx=35c705d10eb3e4055">
# </script>
# <div class="gcse-search"></div>
# https://programmablesearchengine.google.com/controlpanel/overview?cx=35c705d10eb3e4055
export CUSTOM_SEARCH_ENGINE_ID=35c705d10eb3e4055

export CONTAINER_REPOSITORY_NAME=gcr-batch
export CONTAINER_IMAGE_NAME=analyze_and_maintain
export CONTAINER_IMAGE_TAG=latest
export CONTAINER_JOB_NAME=stg-bsp-chatbn-test-gcj

# ・チャネル名：202_バッチ通知用_芝アオイ_開発環境
export NOTIFICATION_URL='https://prod-07.japaneast.logic.azure.com:443/workflows/98f9f0f66f424b1f9fec13d810825972/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=TsIpUVha2a07-pl3-PeP5Utrt4k_8IKf2wBkwBD9VKA'
echo "NOTIFICATION_URL $NOTIFICATION_URL"

# export TIMEZONE=Asia/Tokyo
# export LANGUAGE_CODE=ja
# export DEFAULT_MODEL_ID=claude-3-5-sonnet-v2@20241022
# export FAST_MODEL_ID=gemini-1.5-flash-002
# export GEMINI_MODEL_MAX_OUTPUT_TOKENS=4096
# export GEMINI_MODEL_TEMPERATURE=0
# export GEMINI_MODEL_TOPP=0.9
# export CLAUDE35_MODEL_ID=claude-3-5-sonnet-v2@20241022
# export CLAUDE35_MAX_OUTPUT_TOKENS=4096
# export CLAUDE35_LOCATION_ID=us-east5
# export INSTANCE_CONNECTION_NAME=bsp-pb-support-ai-stg:asia-northeast1:stg-pb-support-sql-backend
# export CLOUD_SQL_IP_TYPE=PUBLIC
# export DB_USER=pbadmin
# export DB_PASSWORD='$ka9fU4{HU}~58VO'
# export DB_NAME=pb_customer_service_manage
# export DB_MAX_CONNECTION=20
# export HISTORY_TABLE_NAME=answer_history
# export CLOUD_SQL_TABLE_NAME_TEMPLATE=template
# export CLOUD_LOGGING_LOG_NAME=stg-pb-support-gcl
# export CLOUD_SQL_INSTANCE_IP_OUTGOING=35.187.201.104
# export CHECKLIST_FORMAT_STR=作業チェックリスト
# export MAIL_TEMPLATE_SEARCH_AGENT_ENGINE_ID=stg-pb-support-search-mail_1731251359839
# export CHECKLIST_SEARCH_AGENT_ENGINE_ID=stg-pb-support-search-work_1731251412101
# export SEARCH_AGENT_LOCATION_ID=global
# export SEARCH_AGENT_COLLECTION_ID=default_collection
# export SEARCH_AGENT_SERVING_CONFIG_ID=default_search:search
# export SEARCH_AGENT_PAGE_SIZE=1
# export TEMPLATE_FORMAT_STR=メール文案
# export CASE_SEARCH_AGENT_ENGINE_ID=stg-pb-support-search-inqu_1731251191469
