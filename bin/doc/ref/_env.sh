export PROJECT_ID=bsp-pb-support-ai-stg
export LOCATION_ID=asia-northeast1
export TIMEZONE=Asia/Tokyo
export LANGUAGE_CODE=ja

# VertexAI関連
export DEFAULT_MODEL_ID='claude-3-5-sonnet-v2@20241022'
export FAST_MODEL_ID='gemini-1.5-flash-002'
export GEMINI_MODEL_MAX_OUTPUT_TOKENS=4096
export GEMINI_MODEL_TEMPERATURE=0
export GEMINI_MODEL_TOPP=0.999

export CLAUDE35_MODEL_ID='claude-3-5-sonnet-v2@20241022'
export CLAUDE35_MAX_OUTPUT_TOKENS=4096
export CLAUDE35_LOCATION_ID=us-east5

export INSTANCE_CONNECTION_NAME='bsp-pb-support-ai-stg:asia-northeast1:stg-pb-support-sql-backend'
export CLOUD_SQL_IP_TYPE=PUBLIC
export DB_USER=pbadmin
export DB_PASSWORD='$ka9fU4{HU}~58VO'
export DB_NAME=pb_customer_service_manage
export DB_MAX_CONNECTION=10
export HISTORY_TABLE_NAME='answer_history'
export CLOUD_SQL_TABLE_NAME_TEMPLATE=template
export CLOUD_SQL_INSTANCE_IP_PRIMARY=35.200.102.109
export CLOUD_SQL_INSTANCE_IP_OUTGOING=35.187.201.104

export CLOUD_LOGGING_LOG_NAME=stg-pb-support-gcl

# 検索関連
export CHECKLIST_FORMAT_STR='作業チェックリスト'
export MAIL_TEMPLATE_SEARCH_AGENT_ENGINE_ID=stg-pb-support-search-mail_1730630901015
export CHECKLIST_SEARCH_AGENT_ENGINE_ID=stg-pb-support-search-work_1730630932613
export SEARCH_AGENT_LOCATION_ID=global
export SEARCH_AGENT_COLLECTION_ID=default_collection
export SEARCH_AGENT_SERVING_CONFIG_ID=default_search:search
export SEARCH_AGENT_PAGE_SIZE=1


export BIGQUERY_DATASET_ID=stg_pb_support_bq
export BIGQUERY_TABLE_ID=answer_history
export BIGQUERY_TABLE_NAME=answer_history