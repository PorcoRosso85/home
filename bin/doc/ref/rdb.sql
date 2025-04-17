SELECT
    created_at,
    user_id
FROM
    answer_history
ORDER BY
    created_at DESC
LIMIT
    10;

SELECT
    *
FROM
    answer_history
WHERE
    review_bool = 'true'
    AND output_format = 'メール文案'
ORDER BY
    created_at DESC;

-- review_bool値をすべてtrueにする
UPDATE answer_history
SET
    review_bool = 'true';

SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM
    information_schema.columns
WHERE
    table_name = 'answer_history'
    -- AND table_schema = 'your_schema_name';
;

-- check index of answer_history
SELECT
    indexname,
    indexdef
FROM
    pg_indexes
WHERE
    tablename = 'answer_history';

-- answer_history_backupを作成
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'answer_history_backup') THEN
        CREATE TABLE answer_history_backup (LIKE answer_history INCLUDING ALL);
    END IF;
END $$;

-- データをコピー
INSERT INTO
    answer_history_backup
SELECT
    *
FROM
    answer_history;

-- バックアップをチェック
SELECT
    *
FROM
    answer_history_backup;

--
SELECT
    *
FROM
    pg_indexes
WHERE
    tablename = 'answer_history_backup';

-- answer_history_pkey	CREATE UNIQUE INDEX answer_history_pkey ON public.answer_history USING btree (id)
-- idx_created_at	CREATE INDEX idx_created_at ON public.answer_history USING btree (created_at)
-- create copy of answer_history including index
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'answer_history_copy') THEN
        CREATE TABLE answer_history_copy (LIKE answer_history INCLUDING ALL);
    END IF;
END $$;

SELECT
    *
FROM
    pg_indexes
WHERE
    tablename = 'answer_history_copy';

-- 移行後answer_history Indexが機能していることを確認
--
SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM
    information_schema.columns
WHERE
    table_name = 'answer_history_copy';

-- insert from answer_history to answer_history_copy
INSERT INTO
    answer_history_copy
SELECT
    *
FROM
    answer_history;

-- 移行後テーブル修正
--
-- before of answer_history_copy
-- column_name data_type character_maximum_length is_nullable column_default
-- id	integer	(null)	NO	nextval('answer_history_id_seq'::regclass)
-- created_at	timestamp without time zone	(null)	YES	CURRENT_TIMESTAMP
-- updated_at	timestamp without time zone	(null)	YES	CURRENT_TIMESTAMP
-- considerations	ARRAY	(null)	NO	(null)
-- query	text	(null)	NO	(null)
-- prompt	text	(null)	YES	(null)
-- answer	text	(null)	YES	(null)
-- review_bool	text	(null)	YES	(null)
-- template_id	character varying	255	NO	(null)
-- case_history_id	character varying	255	NO	(null)
-- output_format	character varying	255	NO	(null)
-- category	character varying	255	NO	(null)
--
--
-- after of answer_history_copy I want
-- column_name data_type character_maximum_length is_nullable column_default
-- id	integer	(null)	NO	nextval('answer_history_id_seq'::regclass)
-- created_at	timestamp without time zone	(null)	NO
-- updated_at	timestamp without time zone	(null)	YES
-- considerations	text	(null)	NO	(null)
-- query	text	(null)	NO	(null)
-- prompt	text	(null)	NO	(null)
-- answer	text	(null)	NO	(null)
-- review_bool	text	(null)	YES	(null)
-- template_id	character varying	255	NO	(null)
-- case_history_id	character varying	255	NO	(null)
-- output_format	character varying	255	NO	(null)
-- category	character varying	255	NO	(null)
ALTER TABLE answer_history_copy
ALTER COLUMN created_at
DROP DEFAULT,
ALTER COLUMN created_at
SET NOT NULL,
ALTER COLUMN updated_at
DROP DEFAULT,
ALTER COLUMN considerations TYPE text,
ALTER COLUMN considerations
SET NOT NULL,
ALTER COLUMN query
SET NOT NULL,
ALTER COLUMN prompt
SET NOT NULL,
ALTER COLUMN answer
SET NOT NULL;

-- add new column 'user_id'
ALTER TABLE answer_history_copy
ADD COLUMN user_id character varying(255);

--rename column considerations to consideration
ALTER TABLE answer_history_copy
RENAME COLUMN considerations TO consideration;

-- check data inserted or not
SELECT
    *
FROM
    answer_history_copy
ORDER BY
    created_at DESC;

SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM
    information_schema.columns
WHERE
    table_name = 'answer_history_copy';

-- 最新30件の answer_history_copy.considerationの値を text '会員登録' に置換
UPDATE answer_history_copy
SET
    consideration = '会員登録'
WHERE
    id IN (
        SELECT
            id
        FROM
            answer_history_copy
        ORDER BY
            created_at DESC
        LIMIT
            30
    );

-- drop rows of above
DELETE FROM answer_history_copy
WHERE
    consideration LIKE '%{%';

SELECT
    *
FROM
    answer_history_copy
ORDER BY
    created_at DESC;

-- change table name test
ALTER TABLE answer_history_copy
RENAME TO answer_history_test;

ALTER INDEX answer_history_copy_pkey
RENAME TO answer_history_test_pkey;

-- roleback
ALTER TABLE answer_history_test
RENAME TO answer_history_copy;

ALTER INDEX answer_history_test_pkey
RENAME TO answer_history_copy_pkey;

-- pb_customer_service_manage データベースのテーブル一覧
SELECT
    *
FROM
    information_schema.tables
WHERE
    table_schema = 'pb_customer_service_manage';

-- テーブル名を変更 answer_history -> answer_history_old, answer_history_copy -> answer_history
ALTER TABLE answer_history
RENAME TO answer_history_old;

ALTER INDEX answer_history_pkey
RENAME TO answer_history_old_pkey;

ALTER TABLE answer_history_copy
RENAME TO answer_history;

ALTER INDEX answer_history_copy_pkey
RENAME TO answer_history_pkey;

-- テーブル名を元に戻す answer_history_old -> answer_history, answer_history -> answer_history_copy
ALTER TABLE answer_history
RENAME TO answer_history_copy;

ALTER INDEX answer_history_pkey
RENAME TO answer_history_copy_pkey;

ALTER TABLE answer_history_old
RENAME TO answer_history;

ALTER INDEX answer_history_old_pkey
RENAME TO answer_history_pkey;

-- created_atカラム isNullable trueに設定
ALTER TABLE answer_history
ALTER COLUMN created_at
SET NOT NULL;

-- user_id type from character varying(255) to text
ALTER TABLE answer_history
ALTER COLUMN user_id TYPE text;

-- answer_history
SELECT
    *
FROM
    answer_history
ORDER BY
    created_at DESC;

SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM
    information_schema.columns
WHERE
    table_name = 'answer_history';

-- インデックスが機能しているか確認するクエリ
SELECT
    *
FROM
    pg_indexes
WHERE
    tablename = 'answer_history';

EXPLAIN
SELECT
    *
FROM
    answer_history
WHERE
    created_at::timestamp = '2023-10-01T12:34:56Z'::timestamp;

-- drop table 'answer_history_old', 'answer_history_backup'
DROP TABLE answer_history_old;

-- 削除するテーブルに、FK依存がないことを確認する
SELECT
    c.conname AS constraint_name,
    c.contype AS constraint_type,
    t.relname AS table_name,
    a.attname AS column_name
FROM
    pg_constraint c
    JOIN pg_class t ON c.conrelid = t.oid
    JOIN pg_attribute a ON a.attnum = ANY (c.conkey)
    AND a.attrelid = t.oid
WHERE
    c.confrelid = 'answer_history_old'::regclass;

-- 1. ビューの依存関係を確認
-- ビューが answer_history_old テーブルに依存しているかどうかを確認します。
SELECT
    c.relname AS view_name,
    pg_get_viewdef(c.oid) AS view_definition
FROM
    pg_class c
    JOIN pg_depend d ON d.refobjid = c.oid
WHERE
    d.objid = 'answer_history_old'::regclass
    AND d.deptype = 'i';

-- 2. トリガーの依存関係を確認
-- トリガーが answer_history_old テーブルに依存しているかどうかを確認します。
SELECT
    tgname AS trigger_name,
    tgrelid::regclass AS table_name
FROM
    pg_trigger
WHERE
    tgrelid = 'answer_history_old'::regclass;

-- 3. 関数の依存関係を確認
-- 関数が answer_history_old テーブルに依存しているかどうかを確認します。
SELECT
    p.proname AS function_name,
    pg_get_functiondef(p.oid) AS function_definition
FROM
    pg_proc p
    JOIN pg_depend d ON d.objid = p.oid
WHERE
    d.refobjid = 'answer_history_old'::regclass
    AND d.deptype = 'i';

-- 特殊な依存オブジェクト
SELECT
    *
FROM
    pg_depend
WHERE
    refobjid = 'answer_history_old'::regclass;

-- ロックやトランザクションの影響を確認
SELECT
    *
FROM
    pg_locks
WHERE
    relation = 'answer_history_old'::regclass;

-- 詳細なエラー情報を確認 PostgreSQLのpg_dependで詳細な依存情報を調査:
SELECT
    classid::regclass AS object_type,
    objid::regclass AS object_name,
    refclassid::regclass AS referenced_type,
    refobjid::regclass AS referenced_name,
    deptype
FROM
    pg_depend
WHERE
    refobjid = 'answer_history_old'::regclass;

-- answer_history_oldに依存しているシーケンスの削除
-- answer_history_oldの answer_history_id_seq が依存しているので、これも削除してよいかチェック
SELECT
    *
FROM
    pg_class
WHERE
    relname = 'answer_history_id_seq';

--
SELECT
    d.classid::regclass AS dependent_object_type,
    d.objid::regclass AS dependent_object_name,
    d.refclassid::regclass AS referenced_object_type,
    d.refobjid::regclass AS referenced_object_name,
    d.deptype
FROM
    pg_depend d
WHERE
    d.refobjid = 'answer_history_id_seq'::regclass;

-- 
SELECT
    c.oid::regclass AS sequence_name,
    n.nspname AS schema_name,
    a.attrelid::regclass AS table_name,
    a.attname AS column_name
FROM
    pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    LEFT JOIN pg_attrdef ad ON ad.adrelid = c.oid
    LEFT JOIN pg_attribute a ON a.attnum = ad.adnum
    AND a.attrelid = ad.adrelid
WHERE
    c.relkind = 'S'
    AND c.oid = 16860;

--
SELECT
    *
FROM
    pg_depend
WHERE
    objid = 16860;

-- 詳細なエラー情報を確認 PostgreSQLのpg_dependで詳細な依存情報を調査:
SELECT
    classid::regclass AS object_type,
    objid::regclass AS object_name,
    refclassid::regclass AS referenced_type,
    refobjid::regclass AS referenced_name,
    deptype
FROM
    pg_depend
WHERE
    refobjid = 'answer_history_old'::regclass;

-- answer_history_oldに依存している type を削除
SELECT
    *
FROM
    pg_depend
WHERE
    refobjid = 16863;

SELECT
    *
FROM
    pg_depend
WHERE
    objid = 16862;

DROP TYPE typename;

-- 16863 の型名を指定
-- answer_history_oldをリネーム
ALTER TABLE answer_history_old
RENAME TO answer_history_old_old;

-- リネームを戻す
ALTER TABLE answer_history_old_old
RENAME TO answer_history_old;

-- answer_history_old_を削除
ALTER TABLE answer_history_old
ALTER COLUMN id
DROP DEFAULT;

DROP TABLE answer_history_old;

DROP TABLE answer_history_old CASCADE;

-- 
SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM
    information_schema.columns
WHERE
    table_name = 'answer_history';

-- answer_history
SELECT
    *
FROM
    answer_history
ORDER BY
    created_at DESC;

SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM
    information_schema.columns
WHERE
    table_name = 'answer_history_backup';

-- answer_history_backupを削除
DROP TABLE answer_history_backup;

--
CREATE SEQUENCE answer_history_id_seq START
WITH
    1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;

ALTER TABLE answer_history
ALTER COLUMN id
SET DEFAULT nextval('answer_history_id_seq');

SELECT
    setval('answer_history_id_seq', 1115);

--
SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM
    information_schema.columns
WHERE
    table_name = 'answer_history';

-- user_idカラムを isNullable=false に設定
ALTER TABLE answer_history
ALTER COLUMN user_id
SET NOT NULL;

-- user_idカラムの値を変更
UPDATE answer_history
SET
    user_id = 'tetsuya.takasawa@zdh.co.jp';

-- user_idカラムが not nullレコードを取得
SELECT
    *
FROM
    answer_history
WHERE
    user_id IS NULL;