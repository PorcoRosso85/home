# detail

目次

- [detail](#detail)
  - [環境変数](#環境変数)
  - [機能設計](#機能設計)
    - [分析結果保存機能](#分析結果保存機能)
      - [前提条件](#前提条件)
      - [処理フロー](#処理フロー)
      - [改善点](#改善点)
    - [最新集計日メンテナンス機能](#最新集計日メンテナンス機能)
      - [前提条件](#前提条件-1)
      - [処理フロー](#処理フロー-1)
    - [コメント再生成機能](#コメント再生成機能)
      - [前提条件](#前提条件-2)
      - [処理フロー](#処理フロー-2)

## 環境変数

|                                      |                                          |
| :----------------------------------- | ---------------------------------------- |
| LOG_EXECUTION_ID                     | ログ出力のオンかオフか                   |
| PROJECT_ID                           | プロジェクトID                           |
| LOCATION_ID                          | ロケーションID                           |
| TIMEZONE                             | タイムゾーン                             |
| LANGUAGE_CODE                        | 言語コード                               |
| DEFAULT_MODEL_ID                     | デフォルトモデルID                       |
| FAST_MODEL_ID                        | ファストモデルID                         |
| GEMINI_MODEL_MAX_OUTPUT_TOKENS       | ジェミニモデルの最大出力トークン数       |
| GEMINI_MODEL_TEMPERATURE             | ジェミニモデルの温度                     |
| GEMINI_MODEL_TOPP                    | ジェミニモデルのTOPP                     |
| CLAUDE35_MODEL_ID                    | クロードモデルID                         |
| CLAUDE35_MAX_OUTPUT_TOKENS           | クロードモデルの最大出力トークン数       |
| CLAUDE35_LOCATION_ID                 | クロードモデルのロケーションID           |
| INSTANCE_CONNECTION_NAME             | インスタンス接続名                       |
| CLOUD_SQL_IP_TYPE                    | Cloud SQL IPアドレスの種類               |
| DB_USER                              | データベースユーザー名                   |
| DB_PASSWORD                          | データベースパスワード                   |
| DB_NAME                              | データベース名                           |
| DB_MAX_CONNECTION                    | データベース最大接続数                   |
| HISTORY_TABLE_NAME                   | 回答履歴テーブル名                       |
| CLOUD_SQL_TABLE_NAME_TEMPLATE        | テンプレートテーブル名                   |
| CLOUD_LOGGING_LOG_NAME               | Cloud Loggingログ名                      |
| CLOUD_SQL_INSTANCE_IP_OUTGOING       | Cloud SQLインスタンス外部IP              |
| CHECKLIST_FORMAT_STR                 | チェックリスト形式                       |
| MAIL_TEMPLATE_SEARCH_AGENT_ENGINE_ID | メールテンプレートエージェントエンジンID |
| CHECKLIST_SEARCH_AGENT_ENGINE_ID     | チェックリストエージェントエンジンID     |
| SEARCH_AGENT_LOCATION_ID             | エージェントロケーションID               |
| SEARCH_AGENT_COLLECTION_ID           | エージェントコレクションID               |
| SEARCH_AGENT_SERVING_CONFIG_ID       | エージェントサービス設定ID               |
| SEARCH_AGENT_PAGE_SIZE               | エージェントページサイズ                 |
| TEMPLATE_FORMAT_STR                  | メール文案                               |
| CASE_SEARCH_AGENT_ENGINE_ID          | ケースエージェントエンジンID             |

|                                      |                                          |
| :----------------------------------- | ---------------------------------------- |
| MAX_RETRIES                          | リトライ回数                             |
| RETRY_DELAY_SECONDS                  | リトライ間隔(秒)                         |
| WEBHOOK_URL                          | Webhook URL                              |
| AZURE_BING_API_KEY                   | Azure Bing API Key                       |
| BIGQUERY_PROJECT_ID                  | BigQuery プロジェクトID                   |
| BIGQUERY_DATASET_ID                  | BigQuery データセットID                   |
| BIGQUERY_TABLE_ID                   | BigQuery テーブルID                      |

## 機能設計

### 分析結果保存機能

Web記事データ取得+大規模言語モデルによる分析結果をストレージへ格納する機能
本機能は日次バッチとしてスケジューリングされている
基本構成は以下の通り

- Cloud Runコンテナ上で本機能を実行
- Cloud Schedulerにより日次バッチを実行
- BigQueryへの格納

- 分析結果保存
- -
- analysis
- FN0001

#### 前提条件

- Cloud Runの実行がスケジュールされている
- BigQuery上に以下データが格納されている
  - 分析のための情報
    - 全IP一覧
    - 最新集計日

#### 処理フロー
<!-- TODO 取得処理にもトランザクションいる？ -->
コメント作成対象IP一覧取得<br/>
begin_transaction()でトランザクション開始<br/>
commit_transaction()でトランザクションコミット<br/>

- 引数
  - BigQueryクライアント
  - コメント処理未完了IPを取得するクエリ
  - _
- 環境変数
  - BIGQUERY_PROJECT_ID
  - BIGQUERY_DATASET_ID
  - BIGQUERY_TABLE_ID
  - MAX_RETRIES
- 異常終了
  - BigQueryErrorをログ
  - **リトライ戦略：指数バックオフ、最大リトライ回数`MAX_RETRIES` (環境変数 MAX_RETRIES 参照)**
  - rollback_transaction()でトランザクションロールバック

Web記事データ取得

- 引数
  - BingSearchクライアント
  - _
  - _
- 環境変数
  - AZURE_BING_API_KEY
  - MAX_RETRIES
  - _
  - _
- 異常終了
  - BingSearchErrorをログ
  - **リトライ戦略：指数バックオフ、最大リトライ回数`MAX_RETRIES` (環境変数 MAX_RETRIES 参照)**
  - _

関連記事の抽出生成<br/>
関連記事がない場合は、関連記事なしとしてコメント指定

- 引数
  - VertexAiクライアント
  - 対象IP一覧
  - Web記事データ
- 環境変数
  - CLAUDE35_MODEL_ID
  - CLAUDE35_MAX_OUTPUT_TOKENS
  - CLAUDE35_LOCATION_ID
  - GEMINI_MODEL_MAX_OUTPUT_TOKENS
  - GEMINI_MODEL_TEMPERATURE
  - GEMINI_MODEL_TOPP
  - MAX_RETRIES
- 異常終了
  - VertexAiErrorをログ
  - **リトライ戦略：指数バックオフ、最大リトライ回数`MAX_RETRIES` (環境変数 MAX_RETRIES 参照)**
  - _

<!-- TODO 分析対象の条件にメンション数があるのでそれも考慮する, バズっていないのに分析してはいけない -->
コメント付加を完了した構造データを生成

- 引数
  - VertexAiクライアント
  - 関連記事の抽出生成結果
  - _
- 環境変数
  - GEMINI_MODEL_MAX_OUTPUT_TOKENS
  - GEMINI_MODEL_TEMPERATURE
  - GEMINI_MODEL_TOPP
  - MAX_RETRIES
- 異常終了
  - VertexAiErrorをログ
  - **リトライ戦略：指数バックオフ、最大リトライ回数`MAX_RETRIES` (環境変数 MAX_RETRIES 参照)**
  - _

構造データをデータベースに格納<br/>
begin_transaction()でトランザクション開始<br/>
commit_transaction()でトランザクションコミット<br/>

- 引数
  - BigQueryクライアント
  - 構造データ
  - 格納するためのクエリ
- 環境変数
  - BIGQUERY_PROJECT_ID
  - BIGQUERY_DATASET_ID
  - BIGQUERY_TABLE_ID
  - MAX_RETRIES
- 異常終了
  - BigQueryErrorをログ
  - **リトライ戦略：指数バックオフ、最大リトライ回数`MAX_RETRIES` (環境変数 MAX_RETRIES 参照)**
  - rollback_transaction()でトランザクションロールバック

<!-- ! -->
処理完了通知をWebhook送信
[link](https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook?tabs=newteams%2Cdotnet)
[link]()

- 引数
  - Webhookクライアント
  - 処理完了通知メッセージ / json
  - _
- 環境変数
  - WEBHOOK_URL
  - MAX_RETRIES
  - _
  - _
- 異常終了
  - WebhookErrorをログ
  - **リトライ戦略：指数バックオフ、最大リトライ回数`MAX_RETRIES` (環境変数 MAX_RETRIES 参照)**
  - _

正常終了ログ出力: 処理コードが0である場合、'Cloud Logging'リソースへ下記「メッセージ」をログ記録する。
<!-- TODO 正常終了Webhook出力 -->

- 引数
  - CloudLoggingクライアント
- 環境変数
  - CLOUD_LOGGING_LOG_NAME
- 内容
  - code: 0
  - message: {機能ID: FN0001, 機能名: analysis_batch, メッセージ: 分析取得保存が正常終了しました。, エラー: 各エラーメッセージ}

異常終了ログ出力: 処理コードが0以外である場合、'Cloud Logging'リソースへ下記「メッセージ」をログ記録する。

- 引数
  - CloudLoggingクライアント
- 環境変数
  - CLOUD_LOGGING_LOG_NAME
- 内容
  - code: 各エラーコード
  - message: {機能ID: FN0001, 機能名: analysys_batch, メッセージ: 分析取得保存が異常終了しました。, エラー: 各エラーメッセージ}

#### 改善点

<!-- 2. 各処理のエラーハンドリングは詳細に記述されているが、リトライ戦略や回復メカニズムが不明確 **(各外部サービスへのアクセスに指数バックオフと最大リトライ回数`MAX_RETRIES` を適用)** -->
<!-- 3. WebhookとCloud Loggingの重複したログ出力戦略の整理が必要 -->
<!-- 4. 異常系のエラーコード体系が曖昧（各エラーコードの定義が不明） -->
<!-- 7. 処理の各ステップ間のデータ引き渡しと依存関係の明確化が必要 -->
<!-- 8. エラー処理の統一化
    - 各処理ごとに異常終了時のログ記録が個別に記載されているが、エラー処理を共通化することで重複を排除し、メンテナンス性を向上させる。
    - 例えば、エラーコードやエラーメッセージを一元管理する仕組みを導入する。 -->
<!-- 9. 環境変数の使用管理
    - 各処理で多数の環境変数を参照しているが、これらの変数を一元的に管理し、初期化時に検証を行う仕組みを追加すると安全性が向上する。
    - 不要な環境変数（例: 使用されていない変数がないか）を明確にする。 -->
<!-- 10. BigQueryのトランザクション管理
    - BigQueryのクライアント操作において、トランザクションが必要か検討すべき。処理中断時の一貫性を保証するため、可能であればバッチ処理全体をトランザクションに包む。
      - BigQueryでは、従来のトランザクションはサポートされていませんが、代わりにbegin_transaction() and commit_transaction()を使用して擬似的なトランザクションを実現できます -->
<!-- 11. データ検証の強化
    - 入出力データのスキーマ検証を設計に追加することで、異常値による障害を未然に防ぐ。
    - 特にVertex AIやBing Search APIのレスポンスデータ構造のチェックを強化。 -->
<!-- 12. 処理フローの冗長性削減
    - "関連記事がない場合は、関連記事なしとしてコメント指定" のようなロジックは統一的なデフォルト処理として抽象化できる可能性がある。 -->
<!-- 13. ログメッセージの詳細化
    - 正常終了・異常終了ログのメッセージ構造に冗長性があるため、必要最小限にしつつ、エラーのトレーサビリティを担保できる内容を記載。 -->
<!-- 14. Webhook送信のリトライ戦略
    - Webhook送信の異常終了時にリトライ機能を組み込む。これにより一時的なネットワーク障害に対応可能。 -->
<!-- 17. 処理コードの冗長な記載の排除
    - "正常終了ログ出力" と "異常終了ログ出力" のコード: 冗長な記述を共通化し、処理コードとログ内容の組み合わせを動的に生成する。 -->

### 最新集計日メンテナンス機能

上記分析取得保存機能が必要とする最新集計日情報を更新するBigQueryへの定期実行処理

- 最新集計日メンテナンス
- -
- aggregates_maintenance
- FN0002

#### 前提条件

- Cloud Runの実行がスケジュールされている
- BigQuery上に以下データが格納されている
  - メンテナンス対象となるIPとその最新集計日

#### 処理フロー

全IPに関して、コメントがある最新集計日を取得するクエリを生成

- 引数
  - BigQueryクライアント
  - IP一覧
  -
- 環境変数
  - BIGQUERY_PROJECT_ID
  - BIGQUERY_DATASET_ID
  - BIGQUERY_TABLE_ID
  - MAX_RETRIES
- 異常終了
  - BigQueryErrorをログ
  - **リトライ戦略：指数バックオフ、最大リトライ回数`MAX_RETRIES` (環境変数 MAX_RETRIES 参照)**
  - rollback_transaction()でトランザクションロールバック

最新集計日メンテナンス実行

- 引数
  - BigQueryクライアント
  - コメント処理未完了IPを取得するクエリ
  - _
- 環境変数
  - BIGQUERY_PROJECT_ID
  - BIGQUERY_DATASET_ID
  - BIGQUERY_TABLE_ID
  - MAX_RETRIES
- 異常終了
  - BigQueryErrorをログ
  - **リトライ戦略：指数バックオフ、最大リトライ回数`MAX_RETRIES` (環境変数 MAX_RETRIES 参照)**
  - rollback_transaction()でトランザクションロールバック

### コメント再生成機能

指定日数過去遡ってコメントを再生成するAPI機能

POST /api/regenerate_comments

```json
リクエスト
{
  "ip": str,
  "start_date": str,
  "end_date": str,
}

レスポンス
{
  "message": str,
}

ヘッダ
{
  "Content-Type": "application/json",
}
```

- コメント再生成
- regenerate_comments
- regenerate_comments
- FN0003

#### 前提条件

- Cloud Run Functionが実行されており、APIへのリクエストを受け取れる状態である
- BigQuery上に以下データが格納されている
  - 分析結果

コンテンツタイプ

- application/json

#### 処理フロー

パラメータバリデーション

- 引数
  - CloudRunからのリクエスト情報
  - バリデーション条件
  - _
- 環境変数
  - BIGQUERY_PROJECT_ID
  - BIGQUERY_DATASET_ID
  - BIGQUERY_TABLE_ID
  - MAX_RETRIES
- 異常終了
  - ValidationErrorをログ
  - 400 / ValidationErrorをレスポンス
  - _

全IPに対して指定日付まで遡って更新対象レコードを取得するクエリを生成

- 引数
  - CloudRunからのリクエスト情報
  - BigQueryクライアント
  - _
- 環境変数
  - BIGQUERY_PROJECT_ID
  - BIGQUERY_DATASET_ID
  - BIGQUERY_TABLE_ID
  - MAX_RETRIES
- 異常終了
  - BigQueryErrorをログ
  - **リトライ戦略：指数バックオフ、最大リトライ回数`MAX_RETRIES` (環境変数 MAX_RETRIES 参照)**
  - rollback_transaction()でトランザクションロールバック

コメント再生成を実行

- 引数
  - BigQueryクライアント
  - 更新対象レコードのクエリ
  - _
- 環境変数
  - BIGQUERY_PROJECT_ID
  - BIGQUERY_DATASET_ID
  - BIGQUERY_TABLE_ID
  - MAX_RETRIES
- 異常終了
  - BigQueryErrorをログ
  - **リトライ戦略：指数バックオフ、最大リトライ回数`MAX_RETRIES` (環境変数 MAX_RETRIES 参照)**
  - rollback_transaction()でトランザクションロールバック
