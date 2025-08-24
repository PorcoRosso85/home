#!/bin/bash
# KuzuDBセットアップスクリプト
# 法人番号データをグラフDBとして構築

set -e

KUZU_DB="./data/corporate_graph.db"
DATA_DIR="./data"

echo "🔧 KuzuDB Setup for Corporate Data"
echo "=================================="

# 1. Create KuzuDB database and schema
echo "1️⃣ Creating KuzuDB schema..."

cat << 'EOF' | nix shell nixpkgs#kuzu -c kuzu_shell $KUZU_DB
// ========================================
// Node Tables (ノード定義)
// ========================================

// 法人エンティティ
CREATE NODE TABLE IF NOT EXISTS Corporation(
    corporate_number STRING PRIMARY KEY,
    corporate_name STRING,
    corporate_name_kana STRING,
    corporate_name_en STRING,
    postal_code STRING,
    prefecture_code STRING,
    city_code STRING,
    street_address STRING,
    registration_date DATE,
    close_date DATE,
    status STRING DEFAULT 'active'
);

// 都道府県マスタ
CREATE NODE TABLE IF NOT EXISTS Prefecture(
    prefecture_code STRING PRIMARY KEY,
    prefecture_name STRING,
    region STRING
);

// 市区町村マスタ  
CREATE NODE TABLE IF NOT EXISTS City(
    city_code STRING PRIMARY KEY,
    city_name STRING,
    prefecture_code STRING
);

// 記事（スクレイピング結果）
CREATE NODE TABLE IF NOT EXISTS Article(
    article_id INT64 PRIMARY KEY,
    source STRING,
    title STRING,
    url STRING,
    scraped_at TIMESTAMP,
    content TEXT
);

// ========================================
// Relationship Tables (リレーション定義)
// ========================================

// 法人→都道府県
CREATE REL TABLE IF NOT EXISTS LOCATED_IN_PREF(
    FROM Corporation TO Prefecture
);

// 法人→市区町村
CREATE REL TABLE IF NOT EXISTS LOCATED_IN_CITY(
    FROM Corporation TO City
);

// 法人→記事での言及
CREATE REL TABLE IF NOT EXISTS MENTIONED_IN(
    FROM Corporation TO Article,
    confidence DOUBLE DEFAULT 1.0,
    mention_type STRING
);

// 法人間の関係（同一住所、親子会社等）
CREATE REL TABLE IF NOT EXISTS RELATED_TO(
    FROM Corporation TO Corporation,
    relation_type STRING,
    strength DOUBLE DEFAULT 1.0
);

.quit
EOF

echo "✅ Schema created"

# 2. Import master data
echo "2️⃣ Importing master data..."

# 都道府県マスタ作成
cat << 'EOF' > $DATA_DIR/prefectures.csv
prefecture_code,prefecture_name,region
"22","静岡県","中部"
"23","愛知県","中部"
"13","東京都","関東"
"27","大阪府","関西"
EOF

# 市区町村マスタ作成（サンプル）
cat << 'EOF' > $DATA_DIR/cities.csv
city_code,city_name,prefecture_code
"22101","静岡市葵区","22"
"22102","静岡市駿河区","22"
"22103","静岡市清水区","22"
"22202","浜松市中区","22"
"22203","浜松市東区","22"
"22220","浜松市南区","22"
EOF

cat << 'EOF' | nix shell nixpkgs#kuzu -c kuzu_shell $KUZU_DB
// Import master data
COPY Prefecture FROM '$DATA_DIR/prefectures.csv' (header=true);
COPY City FROM '$DATA_DIR/cities.csv' (header=true);
.quit
EOF

echo "✅ Master data imported"

# 3. Import corporation data
echo "3️⃣ Importing corporation data..."

# CSVからCorporationテーブルへのマッピング
cat << 'EOF' | nix shell nixpkgs#kuzu -c kuzu_shell $KUZU_DB
// Import corporations from houjin CSV
LOAD FROM '$DATA_DIR/shizuoka_sample.csv' (header=true)
CREATE (:Corporation {
    corporate_number: corporateNumber,
    corporate_name: corporateName,
    corporate_name_kana: corporateNameKana,
    corporate_name_en: corporateNameEn,
    postal_code: postalCode,
    prefecture_code: prefectureCode,
    city_code: cityCode,
    street_address: streetNumber,
    registration_date: date(assignmentDate),
    status: CASE WHEN closeDate = '' THEN 'active' ELSE 'closed' END
});
.quit
EOF

echo "✅ Corporation data imported"

# 4. Build relationships
echo "4️⃣ Building relationships..."

cat << 'EOF' | nix shell nixpkgs#kuzu -c kuzu_shell $KUZU_DB
// Connect corporations to prefectures
MATCH (c:Corporation), (p:Prefecture)
WHERE c.prefecture_code = p.prefecture_code
CREATE (c)-[:LOCATED_IN_PREF]->(p);

// Connect corporations to cities
MATCH (c:Corporation), (city:City)
WHERE c.city_code = city.city_code
CREATE (c)-[:LOCATED_IN_CITY]->(city);

// Find corporations at same address (potential relationships)
MATCH (c1:Corporation), (c2:Corporation)
WHERE c1.corporate_number < c2.corporate_number
  AND c1.postal_code = c2.postal_code
  AND c1.street_address = c2.street_address
CREATE (c1)-[:RELATED_TO {relation_type: 'same_address', strength: 0.9}]->(c2);

.quit
EOF

echo "✅ Relationships built"

# 5. Display summary
echo ""
echo "📊 Database Summary:"
echo "==================="

cat << 'EOF' | nix shell nixpkgs#kuzu -c kuzu_shell $KUZU_DB
// Count nodes
MATCH (c:Corporation) RETURN 'Corporations' as type, COUNT(c) as count
UNION ALL
MATCH (p:Prefecture) RETURN 'Prefectures' as type, COUNT(p) as count
UNION ALL
MATCH (c:City) RETURN 'Cities' as type, COUNT(c) as count;

// Sample corporation data
MATCH (c:Corporation) 
RETURN c.corporate_name, c.prefecture_code, c.city_code 
LIMIT 5;

// Corporations by prefecture
MATCH (c:Corporation)-[:LOCATED_IN_PREF]->(p:Prefecture)
RETURN p.prefecture_name, COUNT(c) as corporation_count
ORDER BY corporation_count DESC;

.quit
EOF

echo ""
echo "✅ KuzuDB setup complete!"
echo ""
echo "次のステップ:"
echo "1. 実際の法人番号CSVをダウンロード"
echo "2. ./data/ に配置"
echo "3. このスクリプトを再実行"
echo ""
echo "分析クエリ例:"
echo "kuzu_shell $KUZU_DB"
echo "> MATCH (c:Corporation) WHERE c.corporate_name CONTAINS 'ヤマハ' RETURN c;"