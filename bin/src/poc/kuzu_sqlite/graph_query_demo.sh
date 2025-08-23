#!/usr/bin/env bash

# SQLiteのリレーショナルデータをKuzuDBでグラフとして探索するデモ
# グラフクエリの能力を確認

set -euo pipefail

WORK_DIR="./data_graph"
SQLITE_DB="$WORK_DIR/social.db"
KUZU_DB="$WORK_DIR/kuzu_graph"

# クリーンアップと準備
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"

echo "=== グラフクエリデモ: ソーシャルネットワーク分析 ==="
echo ""

# 1. SQLiteでソーシャルネットワークデータ作成
echo "1. SQLiteデータベース作成（ソーシャルネットワーク）..."
cat <<EOF | nix shell nixpkgs#sqlite -c sqlite3 "$SQLITE_DB"
-- ユーザーテーブル
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER,
    city TEXT
);

-- フォロー関係テーブル
CREATE TABLE follows (
    follower_id INTEGER,
    followee_id INTEGER,
    since DATE,
    PRIMARY KEY (follower_id, followee_id),
    FOREIGN KEY (follower_id) REFERENCES users(id),
    FOREIGN KEY (followee_id) REFERENCES users(id)
);

-- 投稿テーブル
CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    content TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- いいねテーブル
CREATE TABLE likes (
    user_id INTEGER,
    post_id INTEGER,
    liked_at TIMESTAMP,
    PRIMARY KEY (user_id, post_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (post_id) REFERENCES posts(id)
);

-- サンプルデータ投入
INSERT INTO users (id, name, age, city) VALUES
    (1, 'Alice', 28, 'Tokyo'),
    (2, 'Bob', 32, 'Osaka'),
    (3, 'Carol', 25, 'Tokyo'),
    (4, 'Dan', 30, 'Kyoto'),
    (5, 'Eve', 27, 'Tokyo'),
    (6, 'Frank', 35, 'Osaka');

INSERT INTO follows (follower_id, followee_id, since) VALUES
    (1, 2, '2023-01-15'),  -- Alice follows Bob
    (1, 3, '2023-02-20'),  -- Alice follows Carol
    (2, 1, '2023-01-16'),  -- Bob follows Alice
    (2, 4, '2023-03-10'),  -- Bob follows Dan
    (3, 1, '2023-02-21'),  -- Carol follows Alice
    (3, 5, '2023-04-05'),  -- Carol follows Eve
    (4, 2, '2023-03-11'),  -- Dan follows Bob
    (5, 3, '2023-04-06'),  -- Eve follows Carol
    (5, 6, '2023-05-01'),  -- Eve follows Frank
    (6, 4, '2023-05-15');  -- Frank follows Dan

INSERT INTO posts (id, user_id, content, created_at) VALUES
    (1, 1, 'Hello KuzuDB!', '2024-01-01 10:00:00'),
    (2, 2, 'Graph databases are amazing', '2024-01-02 11:00:00'),
    (3, 3, 'Learning Cypher queries', '2024-01-03 12:00:00'),
    (4, 1, 'SQLite to KuzuDB migration success', '2024-01-04 13:00:00'),
    (5, 4, 'Performance comparison results', '2024-01-05 14:00:00');

INSERT INTO likes (user_id, post_id, liked_at) VALUES
    (2, 1, '2024-01-01 10:30:00'),
    (3, 1, '2024-01-01 11:00:00'),
    (1, 2, '2024-01-02 11:30:00'),
    (4, 2, '2024-01-02 12:00:00'),
    (5, 3, '2024-01-03 12:30:00'),
    (2, 4, '2024-01-04 14:00:00'),
    (3, 4, '2024-01-04 15:00:00'),
    (6, 5, '2024-01-05 15:00:00');

.mode column
.headers on
SELECT 'データ作成完了: ' || COUNT(*) || ' users, ' || 
       (SELECT COUNT(*) FROM follows) || ' follows, ' ||
       (SELECT COUNT(*) FROM posts) || ' posts, ' ||
       (SELECT COUNT(*) FROM likes) || ' likes' AS summary
FROM users;
EOF
echo "✅ SQLiteデータベース作成完了"
echo ""

# 2. KuzuDBでグラフクエリ実行
echo "2. KuzuDBでグラフクエリ実行..."
echo ""

cat <<'EOF' | nix shell nixpkgs#kuzu -c kuzu "$KUZU_DB" 2>/dev/null || true
-- SQLite拡張をロード
INSTALL sqlite;
LOAD sqlite;

-- SQLiteデータベースをアタッチ
ATTACH './social.db' AS social (dbtype sqlite);

-- ===== グラフノードの作成 =====
-- ユーザーをノードとして作成
CREATE NODE TABLE User (
    id INT64 PRIMARY KEY,
    name STRING,
    age INT64,
    city STRING
);

-- 投稿をノードとして作成
CREATE NODE TABLE Post (
    id INT64 PRIMARY KEY,
    content STRING,
    created_at STRING
);

-- ===== グラフエッジの作成 =====
-- フォロー関係
CREATE REL TABLE FOLLOWS (
    FROM User TO User,
    since STRING
);

-- 投稿作成関係
CREATE REL TABLE POSTED (
    FROM User TO Post
);

-- いいね関係
CREATE REL TABLE LIKES (
    FROM User TO Post,
    liked_at STRING
);

-- ===== データのコピー =====
COPY User FROM social.users;
COPY Post FROM (
    SELECT id, content, CAST(created_at AS STRING) AS created_at 
    FROM social.posts
);

COPY FOLLOWS FROM (
    SELECT follower_id AS FROM, followee_id AS TO, CAST(since AS STRING) AS since
    FROM social.follows
);

COPY POSTED FROM (
    SELECT user_id AS FROM, id AS TO
    FROM social.posts
);

COPY LIKES FROM (
    SELECT user_id AS FROM, post_id AS TO, CAST(liked_at AS STRING) AS liked_at
    FROM social.likes
);

-- ===== グラフクエリの実行 =====
-- 1. 相互フォロー関係を見つける
MATCH (u1:User)-[:FOLLOWS]->(u2:User)-[:FOLLOWS]->(u1)
WHERE u1.id < u2.id
RETURN u1.name AS user1, u2.name AS user2, 'mutual' AS relationship;

-- 2. 最も人気のある投稿（いいね数順）
MATCH (p:Post)<-[l:LIKES]-(u:User)
RETURN p.content, COUNT(u) AS like_count
ORDER BY like_count DESC
LIMIT 3;

-- 3. フォロワーの投稿を見る（タイムライン）
MATCH (alice:User {name: 'Alice'})-[:FOLLOWS]->(friend:User)-[:POSTED]->(p:Post)
RETURN friend.name AS author, p.content, p.created_at
ORDER BY p.created_at DESC;

-- 4. 共通のフォロワーを持つユーザーペア
MATCH (u1:User)<-[:FOLLOWS]-(common:User)-[:FOLLOWS]->(u2:User)
WHERE u1.id < u2.id
RETURN u1.name AS user1, u2.name AS user2, COUNT(DISTINCT common) AS common_followers
ORDER BY common_followers DESC;

-- 5. 影響力のあるユーザー（フォロワー数）
MATCH (u:User)<-[:FOLLOWS]-(follower:User)
RETURN u.name, u.city, COUNT(follower) AS follower_count
ORDER BY follower_count DESC;

-- 6. 2ホップ以内の接続（友達の友達）
MATCH path = (alice:User {name: 'Alice'})-[:FOLLOWS*1..2]->(friend:User)
WHERE alice.id != friend.id
RETURN friend.name, LENGTH(path) AS distance
ORDER BY distance, friend.name;

-- 7. 投稿へのエンゲージメント分析
MATCH (u:User)-[:POSTED]->(p:Post)
OPTIONAL MATCH (p)<-[l:LIKES]-(liker:User)
RETURN u.name AS author, p.content, COUNT(l) AS likes
ORDER BY likes DESC;

-- デタッチ
DETACH social;
EOF

echo ""
echo "=== グラフクエリデモ完了 ==="
echo ""
echo "確認できた内容:"
echo "✅ SQLiteリレーショナルデータ → KuzuDBグラフ構造への変換"
echo "✅ ノード（User, Post）とエッジ（FOLLOWS, POSTED, LIKES）の作成"
echo "✅ Cypherパターンマッチングによる複雑なクエリ"
echo "✅ グラフ探索（相互フォロー、共通フォロワー、2ホップ接続など）"