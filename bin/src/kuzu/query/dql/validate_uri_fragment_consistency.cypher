// LocationURIのフラグメント整合性チェッククエリ
// getFragment()で抽出できる情報とDQLで取得できるデータの一致確認

MATCH (uri:LocationURI)
WITH uri.id as id,
     CASE WHEN contains(uri.id, '#') 
          THEN split(uri.id, '#')[2]
          ELSE '' 
     END as cypher_fragment,
     split(uri.id, ':')[1] as cypher_scheme

// TypeScript UriUtils.getFragment()と同じ処理をCypherで再現
WITH id, cypher_fragment, cypher_scheme,
     CASE 
       WHEN cypher_scheme = 'file' AND cypher_fragment =~ '^L\\d+(-L\\d+)?$' THEN 'valid_file_fragment'
       WHEN cypher_scheme = 'requirement' AND cypher_fragment =~ '^REQ-[A-Z0-9]+-\\d+$' THEN 'valid_req_fragment'
       WHEN cypher_scheme = 'test' AND cypher_fragment =~ '^TEST-[A-Z0-9]+-\\d+$' THEN 'valid_test_fragment'
       WHEN cypher_scheme = 'document' AND cypher_fragment =~ '^(section|page)-[a-zA-Z0-9-]+$' THEN 'valid_doc_fragment'
       WHEN cypher_scheme IN ['http', 'https'] THEN 'http_no_validation'
       WHEN cypher_fragment = '' AND cypher_scheme IN ['file', 'requirement', 'test', 'document'] THEN 'missing_required_fragment'
       ELSE 'invalid_fragment_format'
     END as validation_status

RETURN cypher_scheme as scheme,
       cypher_fragment as fragment, 
       validation_status,
       count(*) as count
ORDER BY cypher_scheme, validation_status
