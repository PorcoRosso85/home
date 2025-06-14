code0===
variables...
DEBUG: bool = _validate_variable_str("DEBUG") == "True"
if DEBUG:
print("WARNING: DEBUG environment variable is TRUE now, is it ok?")

PROJECT_ID: str = _validate_variable_str("PROJECT_ID")
PROJECT_REGION: str = _validate_variable_str("PROJECT_REGION")
BIGQUERY_DATASET: str = _validate_variable_str("BIGQUERY_DATASET")
BIGQUERY_TABLE_ID: str = _validate_variable_str("BIGQUERY_TABLE_ID")

GEMINI_MODEL_ID: str = _validate_variable_str("GEMINI_MODEL_ID")
GEMINI_MAX_OUTPUT_TOKENS: int = int(_validate_variable_str("GEMINI_MODEL_MAX_OUTPUT_TOKENS"))
GEMINI_TEMPERATURE: float = float(_validate_variable_str("GEMINI_MODEL_TEMPERATURE"))
GEMINI_TOPP: float = float(_validate_variable_str("GEMINI_MODEL_TOPP"))

CLOUD_STORAGE_BUCKET_NAME: str = _validate_variable_str("CLOUD_STORAGE_BUCKET_NAME")
CLOUD_STORAGE_PARQUET_FILE_NAME: str = _validate_variable_str("CLOUD_STORAGE_PARQUET_FILE_NAME")
CLOUD_STORAGE_AGGREGATION_FILE_NAME: str = _validate_variable_str("CLOUD_STORAGE_AGGREGATION_FILE_NAME")

AZURE_BING_SEARCH_URL: str = _validate_variable_str("AZURE_BING_SEARCH_URL")
AZURE_BING_API_KEY: str = secret.get(PROJECT_ID, "AZURE_BING_API_KEY", "latest")
RETRY_COUNT: int = int(_validate_variable_str("RETRY_COUNT"))
WEB_SITE_SEARCH_DAYS_BEFORE: int = int(_validate_variable_str("WEB_SITE_SEARCH_DAYS_BEFORE"))
WEB_SITE_SEARCH_DAYS_AFTER: int = int(_validate_variable_str("WEB_SITE_SEARCH_DAYS_AFTER"))

NOTIFICATION_URL: str = secret.get(PROJECT_ID, "NOTIFICATION_URL", "latest")
NOTIFICATION_MENTION_MEMBERS: list[str] = secret.get(PROJECT_ID, "NOTIFICATION_MENTION_MEMBERS", "latest")



code1===

def main():

    try:

        """ 

        毎日、全IPを対象に、以下の条件を満たすIPに対するAIコメントを作成する。

            - Xのメンション数 40001 以上 かつ 対前日上昇率0%以上

            - もしくは

            - Xのメンション数 10000 以上 かつ 対前日上昇率150%以上



        バッチ起動時間: 毎日11時30分（日本時間）

        対象集計日: sysdate - 2days

        """



        logging.info('Dairy run job, executed.')



        # AIコメント作成対象のIPを取得するためのSQLを作成する。

        DATE_DELTA = 3

        now = get_datetime.now()

        for d in range(1, DATE_DELTA + 1):

            today = get_datetime.days_ago(days=d, base_date=now)

            dt_today = today.strftime("%Y-%m-%d")

            dt_yesterday = get_datetime.days_ago(days=(d + 1), base_date=now).strftime("%Y-%m-%d")



            logging.info('Get Ips of the AI comment generation.')

            logging.info(f'aggregate date: {dt_today}')



            # AIコメント作成対象のIPを pd.DataFrame 形式で取得。

            bigquery_res = analyze_target.execute_query(aggregate_dt=dt_today, aggregate_dt_yesterday=dt_yesterday)



            # フィルタリングの結果0件である場合分析しない

            if len(bigquery_res) == 0:

                logging.info("No IP was analyzed.")

                notify.send_success("", "ジョブ実行は成功しました！")

                logging.info("Notify to members successfully")

                logging.info("Batch job completed successfully")

                return



            df = pd.DataFrame(data=bigquery_res)

            # SQL側で実施すると複雑になってしまうフィルタリングを実施

            df = df.loc[df['document_cnt_rate_of_inc'] > 0]

            df = df.loc[df['document_cnt_sum'] > df['moving_avg_90_percentile']]

            df = df.loc[df['document_cnt_sum'] >= 10000].reset_index(drop=True)



            logging.info('Execute query is succeeded.')

            logging.info('The num of IP is {}'.format(len(df)))



            logging.debug('response of execution for bigquery is below.')

            logging.debug(df)



            # フィルタリングの結果0件である場合分析しない

            if len(df) == 0:

                logging.info("No IP was analyzed.")

                logging.info("No file was uploaded.")

                notify.send_success("", "ジョブ実行は成功しました！")

                logging.info("Notify to members successfully")

                logging.info("Batch job completed successfully")

                continue



            # 条件を満たしたIPに対して、AIコメントを作成する。

            ip_ids: list[str] = []

            ai_comments: list[Analyzed] = []

            ai_comment_builder = create_comment.AICommentBuilder()

            for i, row in df.iterrows():



                if i >= 1 and variables.DEBUG:

                    break



                logging.info(''.center(80, '='))



                ip_id = row['ip_id']

                ip_name = row['ip_name']

                aggregate_date = row['aggregate_dt']

                # document_cnt = row['document_cnt_sum']



                logging.info('({0}/{1})'.format(i+1, len(df)))

                logging.info(f'IP: {ip_id}')

                logging.info(f'name: {ip_name}')



                analyzed_comment: None | Analyzed = ai_comment_builder.main(ip_id, ip_name, aggregate_date)

                if analyzed_comment is None:

                    continue



                ai_comments.append(analyzed_comment)

                ip_ids.append(ip_id)



                logging.info(''.center(80, '='))



            # 分析結果保存

            file_date = get_datetime.days_ago(days=d-1, base_date=now)

            store.analyzed_results(

                ai_comments,

                variables.CLOUD_STORAGE_BUCKET_NAME,

                file_name.parquet_for_analyzed(file_date)

            )

            logging.info(f"File is stored as: {file_name.parquet_for_analyzed(file_date)}")





        # バッチ完了を通知

        notify.send_success("", "ジョブ実行は成功しました！")

        logging.info("Notify to members successfully")



        # バッチ終了

        logging.info("Batch job completed successfully")



    except WebhookError as e:

        notify.send_error("", variables.NOTIFICATION_MENTION_MEMBERS, "ジョブ実行は失敗しました！")

        logging.error(e, variables.Features.ANALYZE.value, variables.Features.ANALYZE.value)

        raise e

    except BigQueryError as e:

        notify.send_error("", variables.NOTIFICATION_MENTION_MEMBERS, "ジョブ実行は失敗しました！")

        logging.error(e, variables.Features.ANALYZE.value, variables.Features.ANALYZE.value)

        raise e

    except VertexAiError as e:

        notify.send_error("", variables.NOTIFICATION_MENTION_MEMBERS, "ジョブ実行は失敗しました！")

        logging.error(e, variables.Features.ANALYZE.value, variables.Features.ANALYZE.value)

        raise e

    except SearchError as e:

        notify.send_error("", variables.NOTIFICATION_MENTION_MEMBERS, "ジョブ実行は失敗しました！")

        logging.error(e, variables.Features.ANALYZE.value, variables.Features.ANALYZE.value)

        raise e

    except SecretError as e:

        notify.send_error("", variables.NOTIFICATION_MENTION_MEMBERS, "ジョブ実行は失敗しました！")

        logging.error(e, variables.Features.ANALYZE.value, variables.Features.ANALYZE.value)

        raise e

    except StorageError as e:

        notify.send_error("", variables.NOTIFICATION_MENTION_MEMBERS, "ジョブ実行は失敗しました！")

        logging.error(e, variables.Features.ANALYZE.value, variables.Features.ANALYZE.value)

        raise e

    except VariablesError as e:

        notify.send_error("", variables.NOTIFICATION_MENTION_MEMBERS, "ジョブ実行は失敗しました！")

        logging.error(e, variables.Features.ANALYZE.value, variables.Features.ANALYZE.value)

        raise e

    except Exception as e:

        notify.send_error("", variables.NOTIFICATION_MENTION_MEMBERS, "ジョブ実行は失敗しました！")

        logging.error(UnexpectedError(message=f"{e}"), variables.Features.ANALYZE.value, variables.Features.ANALYZE.value)

        raise e



    finally:

        analyze_target.execute_query

        logging.info("Batch job will be down")



    if variables.DEBUG:

        from src.dbg.check_bucket_files import check_bucket_files

        check_bucket_files(

            bucket_name=variables.CLOUD_STORAGE_BUCKET_NAME,

            file_name_analyzed=file_name.parquet_for_analyzed(),

            # file_name_aggregated=file_name.parquet_for_aggregated(),

            # file_name_reanalyzed=file_name.parquet_for_reanalyzed()

        )

    return





code2===

class AICommentBuilder:

def __init__(

self

) -> None:

self.llm = create_llm_answer.LLM()



def exclude_not_related_article(

self,

ip_name: str,

search_bing_data: list

) -> list:

"""

Bing APIで取得した記事データにて「記事タイトル」「記事スニペット」に対象IPの名称が入っていなかったら除外。

"""



related_articles = []

for article in search_bing_data['webPages']['value']:

# if ip_name in article['name'] or ip_name in article['snippet']:

# related_articles.append(article)



# GCP移行後の仕様変更により、フィルタリング処理の除外（器のみ残し）

related_articles.append(article)


return related_articles





def main(

self,

ip_id: str,

ip_name: str,

aggregate_dt: str,

# document_cnt: int,

) -> None | Analyzed:

# 既に対象の「ip_id」、「aggregate_date」のコメントが存在しないかチェック

# WARNING 現在常にFalseを返却する

if dbg.check_already_exists_item(ip_id, aggregate_dt):

logging.debug(f'{ip_id} is already exists in database.')

return



# AIコメントデータ作成

for _ in range(variables.RETRY_COUNT):

try:

# IP名で検索

keyword = f'' + urllib.parse.quote(ip_name).replace('-', '%22')



logging.debug(f'keyword: {keyword}')

logging.debug(f'aggregate_dt: {aggregate_dt}')

# logging.debug(f'document_cnt: {document_cnt}')



# 記事検索期間を指定する

web_search_range_from = datetime.strftime(datetime.strptime(aggregate_dt, '%Y-%m-%d') - timedelta(days=variables.WEB_SITE_SEARCH_DAYS_BEFORE), '%Y-%m-%d')

web_search_range_to = datetime.strftime(datetime.strptime(aggregate_dt, '%Y-%m-%d') + timedelta(days=variables.WEB_SITE_SEARCH_DAYS_AFTER), '%Y-%m-%d')



# Bingからデータを取得する

search_bing_data = bing_search.get_bing_data(keyword, 10, web_search_range_from, web_search_range_to)

logging.debug("search_bing_data")

logging.debug(search_bing_data)



# 「記事タイトル」もしくは「記事スニペット」にアニメ名（keyword）が含まれていなかったら、その記事は除外

related_articles = self.exclude_not_related_article(ip_name, search_bing_data)

logging.debug('関連記事数： {}'.format(len(related_articles)))



if len(related_articles) >= 3:

# LLMに見解コメント作成してもらう（json形式想定）

llm_answer_dict: PredictedItem = self.llm.create_comments_about_a_keyphrase(keyword, related_articles, web_search_range_from, web_search_range_to)

else:

llm_answer_dict = {}

for i, article in enumerate(related_articles, start=1):

llm_answer_dict[str(i)] = {

'article_num': str(i),

'title': article['name'],

'url': article['url'],

'comment': article['snippet']

}



logging.debug('llm_answer_dict')

logging.debug(f"{llm_answer_dict}")



# AIの見解コメント（3記事分に対する）を1つに要約させる

if len(related_articles) != 0:

llm_answer_summary: str = self.llm.summary_comment(llm_answer_dict)

else:

llm_answer_summary = '関連する記事がありませんでした。'



# 「,」を「%d」にエスケープ（AIコメント）

llm_answer_summary = llm_answer_summary.replace('%', '%c').replace(',', '%d')



# タイトル成形

title_list = [

llm_answer_dict[k]['title'].replace('%', '%c').replace(',', '%d')

for k in llm_answer_dict.keys()

]

while len(title_list) < 3:

title_list.append('キーワードに該当する作品タイトルはありませんでした。')

title = ','.join(title_list)

# title = ','.join([

# llm_answer_dict[k]['title'].replace('%', '%c').replace(',', '%d')

# for k in llm_answer_dict.keys()

# ])



# url成形

# LLMが参照した記事番号を使用して、記事生データからURLを取得する。

url_list = []

for k in llm_answer_dict.keys():

article_index = int(llm_answer_dict[k]['article_num']) - 1

url_list.append(related_articles[article_index]['url'])



# url = llm_answer_dict[k]['url']

# if url.find('sample.com') != -1:

# # ハルシネーションにより、ダミーのURLが含まれている場合

# logging.debug('ハルシネーション発生。')

# logging.debug(f'url: {url}')



# try:

# article_index = int(llm_answer_dict[k]['article_num']) - 1

# url_list.append(search_bing_data['webPages']['value'][article_index]['url'])

# except:

# url_list.append(url)

# finally:

# continue

while len(url_list) < 3:

url_list.append('')

url = ','.join(url_list)





comment_data: Analyzed = {

'ip_id': ip_id,

'keyword': ip_name,

# 'count': document_cnt,

'url': url,

'aggregate_date': aggregate_dt,

'title': title,

'comment': llm_answer_summary,

'created_at': get_datetime.now_formatted()

}



return comment_data

except:

e = sys.exc_info()[1]

if _ == variables.RETRY_COUNT - 1:

if isinstance(e, SearchError):

raise SearchError(f"{e}")

else:

raise VertexAiError(f"{e}")

else:

logging.info('Retry.')
