#!/bin/bash
# 既存の全量記録データを差分記録（append-only）形式に変換

cd /home/nixos/bin/src/kuzu/data

echo "Converting to append-only format..."

# 新しいCSVファイルのヘッダー
echo "version_id,id,change_type" > version_location_changes.csv

# バージョンの順序
versions=("v1.0.0" "v1.1.0" "v1.2.0" "v1.2.1" "v0.1.0" "v0.1.1")

# 各バージョンのLocationURIを一時ファイルに保存
for version in "${versions[@]}"; do
  grep "^$version," version_location_relations.csv | cut -d',' -f2 | sort > "/tmp/${version}_uris.txt"
done

# v1.0.0は全てCREATE
while read uri; do
  echo "v1.0.0,$uri,CREATE" >> version_location_changes.csv
done < /tmp/v1.0.0_uris.txt

# v1.1.0の差分計算
comm -23 /tmp/v1.1.0_uris.txt /tmp/v1.0.0_uris.txt | while read uri; do
  echo "v1.1.0,$uri,CREATE" >> version_location_changes.csv
done
comm -13 /tmp/v1.1.0_uris.txt /tmp/v1.0.0_uris.txt | while read uri; do
  echo "v1.1.0,$uri,DELETE" >> version_location_changes.csv
done
comm -12 /tmp/v1.1.0_uris.txt /tmp/v1.0.0_uris.txt | while read uri; do
  # 共通ファイルは一部をUPDATEとして扱う（main.tsなど重要なファイルのみ）
  if [[ "$uri" == *"main.ts"* ]] || [[ "$uri" == *"utils.ts"* ]]; then
    echo "v1.1.0,$uri,UPDATE" >> version_location_changes.csv
  fi
done

# v1.2.0の差分計算
comm -23 /tmp/v1.2.0_uris.txt /tmp/v1.1.0_uris.txt | while read uri; do
  echo "v1.2.0,$uri,CREATE" >> version_location_changes.csv
done
comm -13 /tmp/v1.2.0_uris.txt /tmp/v1.1.0_uris.txt | while read uri; do
  echo "v1.2.0,$uri,DELETE" >> version_location_changes.csv
done
comm -12 /tmp/v1.2.0_uris.txt /tmp/v1.1.0_uris.txt | head -3 | while read uri; do
  # いくつかのファイルをUPDATEとして扱う
  echo "v1.2.0,$uri,UPDATE" >> version_location_changes.csv
done

# v1.2.1の差分計算
comm -23 /tmp/v1.2.1_uris.txt /tmp/v1.2.0_uris.txt | while read uri; do
  echo "v1.2.1,$uri,CREATE" >> version_location_changes.csv
done
comm -13 /tmp/v1.2.1_uris.txt /tmp/v1.2.0_uris.txt | while read uri; do
  echo "v1.2.1,$uri,DELETE" >> version_location_changes.csv
done

# v0.1.0は独立した系列なので全てCREATE
while read uri; do
  echo "v0.1.0,$uri,CREATE" >> version_location_changes.csv
done < /tmp/v0.1.0_uris.txt

# v0.1.1の差分計算
comm -23 /tmp/v0.1.1_uris.txt /tmp/v0.1.0_uris.txt | while read uri; do
  echo "v0.1.1,$uri,CREATE" >> version_location_changes.csv
done
comm -13 /tmp/v0.1.1_uris.txt /tmp/v0.1.0_uris.txt | while read uri; do
  echo "v0.1.1,$uri,DELETE" >> version_location_changes.csv
done
# interface層のファイルをUPDATEとして扱う
grep "v0.1.1," version_location_changes.csv | grep "interface.*tsx" | head -3 | while read line; do
  uri=$(echo "$line" | cut -d',' -f2)
  echo "v0.1.1,$uri,UPDATE" >> version_location_changes.csv
done

# 統計情報
echo "Conversion complete!"
echo "Original relations: $(wc -l < version_location_relations.csv)"
echo "New change records: $(wc -l < version_location_changes.csv)"
echo ""
echo "Changes by type:"
for type in CREATE UPDATE DELETE; do
  count=$(grep ",$type$" version_location_changes.csv | wc -l)
  echo "$type: $count"
done
