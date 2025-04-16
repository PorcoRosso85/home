CREATE TABLE logs AS
SELECT
    *
FROM
    read_json_auto (
        '/root/genai-pb-support-backend/doc/shell/log.json'
    );

-- get all tables
SELECT
    *
FROM
    information_schema.tables;

-- 
SELECT
    jsonPayload.error,
    -- jsonPayload.featureId,
    -- jsonPayload.featureName,
    jsonPayload.message,
    timestamp,
    insertId
    -- *
FROM
    logs
WHERE
    jsonPayload.featureId = 'FN0001'
    -- 正常という文字列を含む
    -- AND jsonPayload.message LIKE '%正常%'
ORDER BY
    timestamp DESC