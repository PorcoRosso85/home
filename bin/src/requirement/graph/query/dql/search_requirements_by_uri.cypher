// URI部分一致による要件検索（バッチ設計）
// 入力: {uri_contains: ["auth", "login"]} - 検索文字列の配列
// 
// 規約準拠:
// - security.md: CONTAINSを使った安全な部分一致検索
// - バッチ設計原則: 1件でも配列で処理

WITH $uri_contains AS search_terms
UNWIND search_terms AS term
WITH DISTINCT term
WHERE term <> ''  // 空文字列を除外

// LocationURIを検索（大文字小文字を区別しない）
MATCH (l:LocationURI)
WHERE toLower(l.id) CONTAINS toLower(term)

// 関連する要件を取得
MATCH (l)-[:LOCATES]->(r:RequirementEntity)

// 結果を収集
WITH r, l, collect(DISTINCT term) AS matched_terms
RETURN r.id AS id,
       r.title AS title,
       r.description AS description,
       r.status AS status,
       l.id AS uri,
       matched_terms,
       size(matched_terms) AS match_count
ORDER BY match_count DESC, r.id