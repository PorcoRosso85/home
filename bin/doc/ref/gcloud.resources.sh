#!/bin/bash

# Cloud Functions
echo "Fetching Cloud Functions..."
gcloud functions list --project=$PROJECT_ID --format=json > cloud_functions.json

# Cloud Logging Logs
echo "Fetching Cloud Logging Logs..."
gcloud logging sinks list --project=$PROJECT_ID --format=json > logging_sinks.json
gcloud logging buckets list --project=$PROJECT_ID --format=json > logging_buckets.json

# Cloud Storage Buckets
echo "Fetching Cloud Storage Buckets..."
# gsutil ls -p $PROJECT_ID > cloud_storage_buckets.txt

# BigQuery Datasets
echo "Fetching BigQuery Datasets..."
# bq ls --project_id=$PROJECT_ID > bigquery_datasets.txt

# Compute Engine Instances
echo "Fetching Compute Engine Instances..."
# gcloud compute instances list --project=$PROJECT_ID --format=json > compute_instances.json
gcloud compute forwarding-rules list --project=$PROJECT_ID --format=json > forwarding_rules.json
gcloud compute backend-services list --project=$PROJECT_ID --format=json > backend_services.json

# All Resources via Cloud Asset Inventory
echo "Fetching All Resources via Cloud Asset Inventory..."
# gcloud asset search-all-resources --scope=projects/$PROJECT_ID --format=json > all_resources.json

# Cloud SQL Instances
echo "Fetching Cloud SQL Instances..."
gcloud sql instances list --project=$PROJECT_ID --format=json > cloud_sql_instances.json

# VPC Networks
echo "Fetching VPC Networks..." 
# VPC ネットワークの一覧を取得
gcloud compute networks list --project=$PROJECT_ID --format=json > vpc_networks.json
# サブネットワークの一覧を取得
gcloud compute networks subnets list --project=$PROJECT_ID --format=json > subnets.json
# ファイアウォールルールの一覧を取得
gcloud compute firewall-rules list --project=$PROJECT_ID --format=json > firewall_rules.json
# ルートの一覧を取得
gcloud compute routes list --project=$PROJECT_ID --format=json > routes.json
# # VPN ゲートウェイの一覧を取得
# gcloud compute vpn-gateways list --project=$PROJECT_ID --format=json > vpn_gateways.json
# # VPN トンネルの一覧を取得
# gcloud compute vpn-tunnels list --project=$PROJECT_ID --format=json > vpn_tunnels.json
# 外部 IP アドレスの一覧を取得
gcloud compute addresses list --project=$PROJECT_ID --format=json > external_ips.json
# 内部 IP アドレスの一覧を取得
# gcloud compute addresses list --project=$PROJECT_ID --filter="addressType=INTERNAL" --format=json > internal_ips.json

echo "Resource fetching completed!"