#!/bin/bash
# 再設計版の読み込みスクリプト

DB="/tmp/kuzu_dev.db"
rm -rf "$DB"

echo "=== Loading redesigned architecture ==="
kuzu "$DB" < schema_clean.cypher

# v2.2をスキップしてv2.2-redesignを使用
for ver in v2.0 v2.0.1 v2.1 v2.2-redesign; do
    if [[ -f "$ver/dml.cypher" ]]; then
        echo "=== Loading $ver ==="
        kuzu "$DB" < "$ver/dml.cypher"
    fi
done

echo
echo "=== Verifying v2.2-redesign for circular dependencies ==="
kuzu "$DB" < v2.2-redesign/dql.cypher 2>&1 | grep -v "Opening" | grep -v "Enter" | tail -20