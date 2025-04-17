code0===

def main(request: Request):
    """ Cloud Functionsのエントリーポイント
    """

    logger.info("API is requested")
    match (request.path, request.method):
        case (variables.Routes.REANALYZE.value, 'POST'):
            try:
                body = request.get_json()
                body = req.validate_body(body)
                reanalyze(body['ip_id'], body['ip_name'], body['aggregate_date'])
                logger.info("API requested has been completed successfully")
                return "Success", 200

            except req.ValidationError as e:
                logger.error(e, variables.Features.REANALYZE.value, variables.Features.REANALYZE.value)
                return str(e), 400
            except Exception as e:
                logger.error(e, variables.Features.REANALYZE.value, variables.Features.REANALYZE.value)
                return str(e), 500
            finally:
                logger.info("API will be down")
        case _:
            logger.error(NotFoundError(f"{request.path}"), variables.Features.REANALYZE.value, variables.Features.REANALYZE.value)
            return "NotFound", 404

def validate_body(body: ReanalyzeRequestBody) -> ReanalyzeRequestBody:
    for key in ['ip_id', 'ip_name', 'aggregate_date']:
        if key not in body:
            raise ValidationError(f"{key}が不足しています。")
        if not isinstance(body[key], str):
            raise ValidationError(f"{key}はstrである必要があります。")

    try:
        get_datetime.date_for_filename( body['aggregate_date'] )
    except Exception as e:
        raise ValidationError(f"{e}")
    return body


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

def reanalyze(ip_id: str, ip_name: str, aggregate_date: str) -> None:
    """リクエスト日時でのコメント再生成"""
    logging.info(''.center(80, '='))

    logging.info(f'IP: {ip_id}')
    logging.info(f'name: {ip_name}')

    ai_comment_builder = create_comment.AICommentBuilder()
    reanalyzed_comment: Analyzed = ai_comment_builder.main(
        ip_id,
        ip_name,
        aggregate_date
    )

    logging.info(''.center(80, '='))

    store.reanalyzed_results(
        [reanalyzed_comment],
        variables.CLOUD_STORAGE_BUCKET_NAME,
        file_name.parquet_for_reanalyzed(
            get_datetime.date_for_filename(aggregate_date)
        )
    )



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
