#!/bin/bash

# post query_and_save
curl -I -X POST localhost:8080/api/query_and_save

# 400
curl -s -D - -H "Content-Type: application/json" -d '{
    "outputFormat": "",
    "category": "",
    "consideration": "",
    "query": ""
}' -X POST localhost:8080/api/query_and_save | jq '.' > response.json
curl -s -D - -H "Content-Type: application/json" -d '{
    "outputFormat": "作業チェックリスト",
    "category": "会員",
    "consideration": "会員",
    "query": ""
}' -X POST localhost:8080/api/query_and_save
curl -s -D - -H "Content-Type: application/json" -d '{
    "outputFormat": "",
    "category": "",
    "consideration": "",
    "query": ""
}' -X POST $FUNCTION_STAGING/api/query_and_save | jq '.' > response.json

# 502 Bad Gateway
curl -s -D - -H "Content-Type: application/json" -d '{
    "outputFormat": "メール文案",
    "category": "会員登録",
    "consideration": "会員登録"
}' -X POST localhost:8080/api/query_and_save -o response.json
# 502 Bad Gateway
curl -s -D - -H "Content-Type: application/json" -d '{
    "outputFormat": "メール文案",
    "category": "会員登録",
    "consideration": "会員登録"
}' -X POST $FUNCTION_STAGING/api/query_and_save -o response.json
curl -s -D - -H "Content-Type: application/json" -d '{
    "outputFormat": "メール文案",
    "category": "会員登録",
    "consideration": "会員登録",
    "query": "退会"
}' -X POST $FUNCTION_STAGING/api/query_and_save -o response.json

# 個人情報を含めたリクエスト
curl -s -D - 
-H "Content-Type: application/json" \
-d '{
    "outputFormat": "メール文案",
    "category": "会員登録",
    "consideration": "会員登録",
    "query": "住所は、東京都千代田区です。"
}' \
-X POST localhost:8080/api/query_and_save | tee /dev/tty | tail -n +9 | jq '.' > response.json
curl -s -D - \
-H "Content-Type: application/json" \
-d '{
    "outputFormat": "メール文案",
    "category": "会員登録",
    "consideration": "会員登録",
    "query": "住所は、東京都千代田区です。"
}' \
-X POST $FUNCTION_STAGING/api/query_and_save | tee /dev/tty | tail -n +9 | jq '.' > response.json


# 200
curl -s -D - \
-H "Content-Type: application/json" \
-d '{
    "outputFormat": "メール文案",
    "category": "会員登録",
    "consideration": "会員登録",
    "query": "退会"
}' -X POST localhost:8080/api/query_and_save | tee /dev/tty | tail -n +9 > response.json
curl -s -D - \
-H "Content-Type: application/json" \
-d '{
    "outputFormat": "メール文案",
    "category": "会員登録",
    "consideration": "会員登録",
    "query": "退会"
}' -X POST $FUNCTION_STAGING/api/query_and_save | tee /dev/tty | tail -n +9 > response.json


# 200, 作業チェックリスト形式の時のメッセージ確認
curl -s -D - \
-H "Content-Type: application/json" \
-d '{
    "outputFormat": "作業チェックリスト",
    "category": "会員登録",
    "consideration": "会員登録",
    "query": "退会"
}' -X POST localhost:8080/api/query_and_save | tee /dev/tty | tail -n +9 | jq '.' > response.json

# 200, gemini指定でtrueが返される問題
# {outputFormat: "メール文案", category: "ID・パスワード", consideration: "2段階認証設定なし", query: "パスワードを失念した",…}
# category : "ID・パスワード"
# consideration : "2段階認証設定なし"
# modelID : "gemini-1.5-pro-002"
# outputFormat : "メール文案"
# query : "パスワードを失念した"
curl -s -D - \
-H "Content-Type: application/json" \
-d '{
    "outputFormat": "メール文案",
    "category": "ID・パスワード",
    "consideration": "2段階認証設定なし",
    "query": "パスワードを失念した",
    "modelID": "gemini-1.5-pro-002"
}' -X POST localhost:8080/api/query_and_save | tee /dev/tty | tail -n +9 | jq '.' > response.json

curl -s -D - \
-H "Content-Type: application/json" \
-d '{
    "outputFormat": "メール文案",
    "category": "ID・パスワード",
    "consideration": "2段階認証設定なし",
    "query": "パスワードを失念した",
    "userEmail": "tetsuya.takasawa@zdh.co.jp"
}' -X POST localhost:8080/api/query_and_save | tee /dev/tty | tail -n +9 | jq '.' > response.json

curl -s -D - \
-H "Content-Type: application/json" \
-d '{
    "outputFormat": "メール文案",
    "category": "ID・パスワード",
    "consideration": "2段階認証設定なし",
    "query": "パスワードを失念した",
    "userEmail": "accounts.google.com:takumi_kamihara@irep.co.jp"
}' -X POST localhost:8080/api/query_and_save

curl -s -D - \
-H "Content-Type: application/json" \
-d '{
    "outputFormat": "作業チェックリスト",
    "category": "ID・パスワード",
    "consideration": "2段階認証設定なし",
    "query": "パスワードを失念した",
    "userEmail": "tetsuya.takasawa@zdh.co.jp"
}' -X POST $FUNCTION_STAGING/api/query_and_save | tee /dev/tty | tail -n +9 | jq '.' > response.json

# get answer_histories_list
curl -X GET localhost:8080/api/answer_histories_list
curl -s -D - -G \
--data-urlencode "query=" \
--data-urlencode "categories=" \
--data-urlencode "keyOrderBy=createdAt" \
--data-urlencode "valueOrderBy=0" \
--data-urlencode "pageSize=10" \
--data-urlencode "pageNumber=1" \
-X GET localhost:8080/api/answer_histories_list \
| tee /dev/tty | tail -n +9 | jq '.' > response.json
curl -s -D - -G \
--data-urlencode "query=" \
--data-urlencode "categories=会員登録,キャンペーン" \
--data-urlencode "keyOrderBy=createdAt" \
--data-urlencode "valueOrderBy=0" \
--data-urlencode "pageSize=10" \
--data-urlencode "pageNumber=999999" \
-X GET localhost:8080/api/answer_histories_list \
| tee /dev/tty | tail -n +11 | jq '.' > response.json
curl -s -D - -G \
--data-urlencode "query=" \
--data-urlencode "categories=会員登録,キャンペーン" \
--data-urlencode "keyOrderBy=createdAt" \
--data-urlencode "valueOrderBy=0" \
--data-urlencode "pageSize=0" \
--data-urlencode "pageNumber=1" \
-X GET localhost:8080/api/answer_histories_list \
| tee /dev/tty | tail -n +11 | jq '.' > response.json

# to deployed
curl -s -D - -G \
--data-urlencode "query=" \
--data-urlencode "categories=会員登録,キャンペーン" \
--data-urlencode "keyOrderBy=createdAt" \
--data-urlencode "valueOrderBy=0" \
--data-urlencode "pageSize=10" \
--data-urlencode "pageNumber=2" \
-X GET $FUNCTION_STAGING/api/answer_histories_list \
| tee /dev/tty | tail -n +11 | jq '.' > response.json

# get answer_history_detail
curl -X GET localhost:8080/api/answer_history_detail
curl -s -D - -H "Content-Type: application/json" -G \
--data-urlencode "answerHistoryId=1112" \
-X GET localhost:8080/api/answer_history_detail | tee /dev/tty | tail -n +11 | jq '.' > response.json
# not found id
curl -s -D - -H "Content-Type: application/json" -G \
--data-urlencode "answerHistoryId=0" \
-X GET localhost:8080/api/answer_history_detail | tee /dev/tty | tail -n +11 | jq '.' > response.json
# not found id
curl -s -D - -H "Content-Type: application/json" -G \
--data-urlencode "answerHistoryId=999999999" \
-X GET localhost:8080/api/answer_history_detail | tee /dev/tty | tail -n +11 | jq '.' > response.json
# 桁数オーバー
curl -s -D - -H "Content-Type: application/json" -G \
--data-urlencode "answerHistoryId=9999999990" \
-X GET localhost:8080/api/answer_history_detail | tee /dev/tty | tail -n +11 | jq '.' > response.json
# not found id
curl -s -D - -H "Content-Type: application/json" -G \
--data-urlencode "answerHistoryId=x" \
-X GET localhost:8080/api/answer_history_detail | tee /dev/tty | tail -n +11 | jq '.' > response.json
# to deployed
curl -s -D - -H "Content-Type: application/json" -G \
--data-urlencode "answerHistoryId=880" \
-X GET $FUNCTION_STAGING/api/answer_history_detail | tee /dev/tty | tail -n +11 | jq '.' > response.json


# post review
curl -s -D - \
-H "Content-Type: application/json" \
-d '{
    "answerHistoryId": 1112,
    "reviewBool": true
}' -X POST localhost:8080/api/review | tee /dev/tty | tail -n +9 | jq '.' > response.json
curl -s -D - \
-H "Content-Type: application/json" \
-d '{
    "answerHistoryId": 1112,
    "reviewBool": false
}' -X POST localhost:8080/api/review | tee /dev/tty | tail -n +9 | jq '.' > response.json

# get selectables
curl -X GET localhost:8080/api/selectables
curl -X GET localhost:8080/api/selectables | grep -i "x-goog-iap-jwt-assertion"
curl -X GET $FUNCTION_STAGING/api/selectables | grep -i "x-goog-iap-jwt-assertion"


# get considerations
curl -X GET localhost:8080/api/considerations
curl -G \
--data-urlencode "outputFormat=メール文案" \
--data-urlencode "category=会員登録" \
--data-urlencode "query=" \
-X GET localhost:8080/api/considerations
curl -G \
--data-urlencode "outputFormat=メール文案" \
--data-urlencode "category=会員登録" \
--data-urlencode "query=" \
-X GET $FUNCTION_STAGING/api/considerations | jq .
curl -G \
--data-urlencode "outputFormat=メール文案" \
--data-urlencode "category=キャンペーン" \
--data-urlencode "query=" \
-X GET $FUNCTION_STAGING/api/considerations | jq .


# post review
curl -s -D - \
-H "Content-Type: application/json" \
-d '{
    "answerHistoryId": 1,
    "reviewBool": true
}' -X POST localhost:8080/api/review | tee /dev/tty | tail -n +9 | jq '.' > response.json
curl -s -D - \
-H "Content-Type: application/json" \
-d '{
    "answerHistoryId": 999999999,
    "reviewBool": true
}' -X POST localhost:8080/api/review | tee /dev/tty | tail -n +9 | jq '.' > response.json


# get csv
curl -X GET localhost:8080/api/csv?answerHistoryId=880,881,882
curl -X GET localhost:8080/api/csv?answerHistoryId=A
curl -X GET $FUNCTION_STAGING/api/csv?answerHistoryId=1,2,3


# get answer_history_info
# 400
curl -s -D - -G \
--data-urlencode "query=" \
--data-urlencode "categories=" \
--data-urlencode "pageSize=0" \
-X GET localhost:8080/api/answer_history_info \
| tee /dev/tty | tail -n +11 | jq '.' > response.json

# 200
curl -s -D - -G \
--data-urlencode "query=" \
--data-urlencode "categories=" \
--data-urlencode "pageSize=10" \
-X GET localhost:8080/api/answer_history_info \
| tee /dev/tty | tail -n +11 | jq '.' > response.json
curl -s -D - -G \
--data-urlencode "query=" \
--data-urlencode "categories=" \
--data-urlencode "pageSize=10" \
-X GET localhost:8080/api/answer_history_info \
| tee /dev/tty | tail -n +11 | jq '.' > response.json

curl -s -D - -G \
--data-urlencode "query=" \
--data-urlencode "categories=" \
--data-urlencode "pageSize=0" \
-X GET $FUNCTION_STAGING/api/answer_history_info \
| tee /dev/tty | tail -n +11 | jq '.' > response.json

curl -s -D - -G \
--data-urlencode "query=" \
--data-urlencode "categories=" \
--data-urlencode "pageSize=10" \
-X GET $FUNCTION_STAGING/api/answer_history_info \
| tee /dev/tty | tail -n +11 | jq '.' > response.json
curl -G \
--data-urlencode "query=" \
--data-urlencode "categories=" \
--data-urlencode "pageSize=1" \
-X GET $FUNCTION_STAGING/api/answer_history_info | jq '.'
curl -G \
--data-urlencode "query=" \
--data-urlencode "categories=" \
--data-urlencode "pageSize=10" \
-X GET $FUNCTION_STAGING/api/answer_history_info | jq '.'

curl -G \
--data-urlencode "query=会員登録" \
--data-urlencode "categories=会員登録,キャンペーン" \
--data-urlencode "pageSize=1" \
-X GET $FUNCTION_STAGING/api/answer_history_info | jq '.'
curl -G \
--data-urlencode "query=会員登録" \
--data-urlencode "categories=会員登録,キャンペーン" \
--data-urlencode "pageSize=10" \
-X GET $FUNCTION_STAGING/api/answer_history_info | jq '.'


curl -v -H "X-Goog-Authenticated-User-Email: accounts.google.com:tetsuya.takasawa@zdh.co.jp" $FUNCTION_STAGING

curl -v \
-H "X-Goog-Authenticated-User-Email: accounts.google.com:tetsuya.takasawa@zdh.co.j" \
-H "Content-Type: application/json" \
-d '{
    "outputFormat": "メール文案",
    "category": "会員登録",
    "consideration": "会員登録",
    "query": "退会"
}' \
-X POST $FUNCTION_STAGING/api/query_and_savecurl -H "Authorization: Bearer $(gcloud auth print-identity-token)" https://stg-bsp-chatbn-test-gcr-1066839057921.asia-northeast1.run.app/analyze

