curl https://charaview-api-v15.azure.charaos.com \
-d '{"ip_id": "IP00002021"}'

curl -s https://charaview-api-v15.azure.charaos.com \
-d '{"ip_id": "IP00002021"}' \
| jq . > ./doc/test/result.json

curl -s https://charaview-recent-aggregates.azure.charaos.com \
| jq . > ./doc/test/recent_aggregates.json