#!/usr/bin/env bash

# SQLiteデータベースの作成とKuzuDBへのアタッチを実行する例
# 必要なCLIツール: sqlite3, kuzu

set -euo pipefail

# 作業ディレクトリ
WORK_DIR="./data"
SQLITE_DB="$WORK_DIR/university.db"
KUZU_DB="$WORK_DIR/kuzu_db"

# ディレクトリ作成
mkdir -p "$WORK_DIR"

# SQLiteデータベースの作成とサンプルデータ投入
echo "=== SQLiteデータベース作成 ==="
cat <<EOF | nix shell nixpkgs#sqlite -c sqlite3 "$SQLITE_DB"
CREATE TABLE IF NOT EXISTS person (
    name VARCHAR PRIMARY KEY,
    age INTEGER
);

INSERT INTO person (name, age) VALUES 
    ('Alice', 30),
    ('Bob', 27),
    ('Carol', 19),
    ('Dan', 25);

CREATE TABLE IF NOT EXISTS course (
    id INTEGER PRIMARY KEY,
    name VARCHAR,
    credits INTEGER
);

INSERT INTO course (id, name, credits) VALUES
    (1, 'Database Systems', 3),
    (2, 'Machine Learning', 4),
    (3, 'Algorithms', 3);

CREATE TABLE IF NOT EXISTS enrollment (
    student_name VARCHAR,
    course_id INTEGER,
    grade VARCHAR,
    FOREIGN KEY (student_name) REFERENCES person(name),
    FOREIGN KEY (course_id) REFERENCES course(id)
);

INSERT INTO enrollment (student_name, course_id, grade) VALUES
    ('Alice', 1, 'A'),
    ('Alice', 2, 'B'),
    ('Bob', 1, 'B'),
    ('Carol', 3, 'A'),
    ('Dan', 2, 'A'),
    ('Dan', 3, 'B');
EOF

echo "SQLiteデータベース作成完了: $SQLITE_DB"

# SQLiteの内容確認
echo ""
echo "=== SQLiteデータベースの内容確認 ==="
echo "person テーブル:"
nix shell nixpkgs#sqlite -c sqlite3 "$SQLITE_DB" "SELECT * FROM person;"

echo ""
echo "course テーブル:"
nix shell nixpkgs#sqlite -c sqlite3 "$SQLITE_DB" "SELECT * FROM course;"

echo ""
echo "enrollment テーブル:"
nix shell nixpkgs#sqlite -c sqlite3 "$SQLITE_DB" "SELECT * FROM enrollment;"

# KuzuDBでSQLiteをアタッチして操作
echo ""
echo "=== KuzuDBでSQLiteをアタッチ ==="

# KuzuDBディレクトリを初期化（既存の場合は削除）
rm -rf "$KUZU_DB"

# KuzuDBでのクエリ実行
cat <<EOF | nix shell nixpkgs#kuzu -c kuzu "$KUZU_DB"
-- SQLite拡張をインストール・ロード
INSTALL sqlite;
LOAD sqlite;

-- SQLiteデータベースをアタッチ
ATTACH '$SQLITE_DB' AS uw (dbtype sqlite);

-- アタッチされたデータベースの確認
SHOW TABLES;

-- SQLiteテーブルから直接データを読み込み
LOAD FROM uw.person RETURN *;

-- JOIN操作の例
LOAD FROM uw.enrollment e
JOIN uw.person p ON e.student_name = p.name
JOIN uw.course c ON e.course_id = c.id
RETURN p.name AS student, c.name AS course, e.grade, p.age
ORDER BY student, course;

-- グラフテーブルの作成とデータのコピー
CREATE NODE TABLE Student (name STRING PRIMARY KEY, age INT64);
CREATE NODE TABLE Course (id INT64 PRIMARY KEY, name STRING, credits INT64);
CREATE REL TABLE Enrolls (FROM Student TO Course, grade STRING);

-- データのコピー
COPY Student FROM uw.person;
COPY Course FROM uw.course;
COPY Enrolls FROM (
    LOAD FROM uw.enrollment 
    RETURN student_name AS FROM, course_id AS TO, grade
);

-- グラフクエリの例（Cypherクエリ）
MATCH (s:Student)-[e:Enrolls]->(c:Course)
WHERE s.age > 25
RETURN s.name, c.name, e.grade;

-- データベースのデタッチ
DETACH uw;
EOF

echo ""
echo "=== 実行完了 ==="
echo "作成されたファイル:"
echo "  - SQLiteデータベース: $SQLITE_DB"
echo "  - KuzuDBデータベース: $KUZU_DB"