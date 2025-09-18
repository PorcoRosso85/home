-- グラフパターンマッチングのサンプルクエリ集
-- KuzuDBでSQLiteデータをグラフとして探索

-- =====================================
-- 基本的なパターンマッチング
-- =====================================

-- 1. 単純なエッジトラバーサル
MATCH (u:User)-[:FOLLOWS]->(f:User)
RETURN u.name AS follower, f.name AS followee;

-- 2. 特定ユーザーのフォロワー
MATCH (alice:User {name: 'Alice'})<-[:FOLLOWS]-(follower:User)
RETURN follower.name, follower.city;

-- =====================================
-- 複雑なパターンマッチング
-- =====================================

-- 3. 三角形の関係（3人が相互にフォロー）
MATCH (a:User)-[:FOLLOWS]->(b:User)-[:FOLLOWS]->(c:User)-[:FOLLOWS]->(a)
WHERE a.id < b.id AND b.id < c.id
RETURN a.name, b.name, c.name;

-- 4. フォロワーチェーン（A→B→C→D）
MATCH path = (start:User)-[:FOLLOWS*3]->(end:User)
WHERE start.name = 'Alice'
RETURN path;

-- =====================================
-- 集約とグループ化
-- =====================================

-- 5. 都市別のユーザー接続数
MATCH (u1:User)-[:FOLLOWS]->(u2:User)
WHERE u1.city = u2.city
RETURN u1.city, COUNT(*) AS intra_city_connections
GROUP BY u1.city;

-- 6. ユーザーごとの投稿といいねの統計
MATCH (u:User)
OPTIONAL MATCH (u)-[:POSTED]->(p:Post)
OPTIONAL MATCH (p)<-[:LIKES]-(l:User)
RETURN u.name, 
       COUNT(DISTINCT p) AS post_count,
       COUNT(l) AS total_likes
ORDER BY total_likes DESC;

-- =====================================
-- パス探索
-- =====================================

-- 7. 最短パス探索
MATCH path = shortestPath((alice:User {name: 'Alice'})-[:FOLLOWS*]-(frank:User {name: 'Frank'}))
RETURN path, LENGTH(path) AS distance;

-- 8. すべてのパス（最大3ホップ）
MATCH path = (alice:User {name: 'Alice'})-[:FOLLOWS*1..3]-(target:User)
WHERE alice.id != target.id
RETURN DISTINCT target.name, MIN(LENGTH(path)) AS min_distance
ORDER BY min_distance;

-- =====================================
-- 条件付きパターン
-- =====================================

-- 9. 年齢フィルタリング付きフォロー関係
MATCH (young:User)-[:FOLLOWS]->(older:User)
WHERE young.age < 30 AND older.age >= 30
RETURN young.name AS younger_user, older.name AS older_user, 
       young.age AS young_age, older.age AS older_age;

-- 10. 同じ都市のユーザー間のインタラクション
MATCH (u1:User)-[:POSTED]->(p:Post)<-[:LIKES]-(u2:User)
WHERE u1.city = u2.city AND u1.id != u2.id
RETURN u1.name, u2.name, u1.city, p.content;

-- =====================================
-- 否定パターン
-- =====================================

-- 11. フォローしていないが共通のフォロワーがいるユーザー
MATCH (u1:User)<-[:FOLLOWS]-(common:User)-[:FOLLOWS]->(u2:User)
WHERE u1.id != u2.id 
  AND NOT EXISTS { MATCH (u1)-[:FOLLOWS]->(u2) }
RETURN u1.name, u2.name, COUNT(DISTINCT common) AS common_followers
ORDER BY common_followers DESC;

-- 12. いいねしていない自分のフォロワーの投稿
MATCH (me:User {name: 'Alice'})-[:FOLLOWS]->(friend:User)-[:POSTED]->(p:Post)
WHERE NOT EXISTS { MATCH (me)-[:LIKES]->(p) }
RETURN friend.name, p.content;

-- =====================================
-- 複雑な分析
-- =====================================

-- 13. インフルエンサー検出（フォロワー多、フォロー少）
MATCH (u:User)
OPTIONAL MATCH (u)<-[:FOLLOWS]-(follower:User)
OPTIONAL MATCH (u)-[:FOLLOWS]->(following:User)
WITH u, COUNT(DISTINCT follower) AS followers, COUNT(DISTINCT following) AS following
WHERE followers > 0
RETURN u.name, followers, following, 
       CASE WHEN following > 0 THEN followers * 1.0 / following ELSE followers END AS influence_ratio
ORDER BY influence_ratio DESC;

-- 14. コミュニティ検出（密接に繋がったグループ）
MATCH (u1:User)-[:FOLLOWS]->(u2:User)-[:FOLLOWS]->(u3:User)
WHERE EXISTS { MATCH (u1)-[:FOLLOWS]->(u3) OR (u3)-[:FOLLOWS]->(u1) }
RETURN u1.name, u2.name, u3.name AS community_members;

-- 15. タイムライン生成（フォローしている人の最近の投稿）
MATCH (me:User {name: 'Alice'})-[:FOLLOWS]->(friend:User)-[:POSTED]->(p:Post)
OPTIONAL MATCH (p)<-[:LIKES]-(liker:User)
RETURN friend.name AS author, p.content, p.created_at,
       COUNT(liker) AS likes
ORDER BY p.created_at DESC
LIMIT 10;