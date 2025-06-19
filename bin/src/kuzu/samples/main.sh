#!/bin/bash
# KuzuDB セマンティックバージョニング管理システム
# MAJOR.MINOR.PATCH 形式で開発計画を管理

DB="${KUZU_DB:-/tmp/kuzu_dev.db}"
SCHEMA_FILE="${KUZU_SCHEMA:-schema_clean.cypher}"

# 使用方法表示
usage() {
    echo "Usage: $0 [command] [version]"
    echo "Commands:"
    echo "  load [version]   - 指定バージョンまでのデータを投入"
    echo "  verify [version] - 指定バージョンの検証を実行"
    echo "  timeline         - 全バージョンのタイムライン表示"
    echo "  clean            - データベースをクリア"
    echo "  list             - 利用可能なバージョン一覧"
    echo "Example: $0 load 2.2.1"
    echo "Version format: MAJOR.MINOR.PATCH (e.g., 2.0.0, 2.1.0, 2.0.1)"
    exit 1
}

# セマンティックバージョンの比較
version_lte() {
    [[ "$1" == "$2" ]] && return 0
    local IFS=.
    local i ver1=($1) ver2=($2)
    for ((i=0; i<3; i++)); do
        if [[ ${ver1[i]} -lt ${ver2[i]} ]]; then
            return 0
        elif [[ ${ver1[i]} -gt ${ver2[i]} ]]; then
            return 1
        fi
    done
    return 0
}

# 利用可能なバージョンを動的に取得
get_available_versions() {
    find . -maxdepth 1 -type d -name "[0-9]*.[0-9]*.[0-9]*" | 
    sed 's|^./||' | 
    sort -V
}

# バージョンまでの累積データ投入
load_until_version() {
    local target=$1
    
    # 既存のDBがあれば削除して再作成（冪等性を保証）
    if [[ -e "$DB" ]]; then
        echo "=== Cleaning existing database ==="
        rm -rf "$DB"
    fi
    
    echo "=== Loading schema ==="
    kuzu "$DB" < "$SCHEMA_FILE"
    
    # 動的にバージョンディレクトリを検出
    local versions=($(get_available_versions))
    local loaded_count=0
    
    for ver in "${versions[@]}"; do
        if [[ -f "$ver/dml.cypher" ]] && version_lte "$ver" "$target"; then
            echo "=== Loading $ver ==="
            kuzu "$DB" < "$ver/dml.cypher"
            ((loaded_count++))
        fi
    done
    
    echo "=== Loaded $loaded_count versions up to $target ==="
}

# 特定バージョンの検証実行
verify_version() {
    local ver=$1
    if [[ -f "$ver/dql.cypher" ]]; then
        echo "=== Verifying $ver ==="
        kuzu "$DB" < "$ver/dql.cypher" 2>&1 | grep -v "Opening" | grep -v "Enter" | tail -20
    else
        echo "Error: No verification query for version $ver"
    fi
}

# タイムライン表示（動的クエリ生成）
show_timeline() {
    echo "=== Development Timeline ==="
    {
        echo "MATCH (v:VersionState)"
        echo "OPTIONAL MATCH (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc:LocationURI)"
        echo "WITH v, count(loc) as file_count"
        echo "RETURN v.id as version, v.timestamp as date, v.description, file_count"
        echo "ORDER BY v.timestamp;"
    } | kuzu "$DB" 2>&1 | grep -v "Opening" | grep -v "Enter" | tail -20
}

# 利用可能なバージョン一覧表示
list_versions() {
    echo "=== Available Versions ==="
    local versions=($(get_available_versions))
    for ver in "${versions[@]}"; do
        local status=""
        [[ -f "$ver/dml.cypher" ]] && status="${status}[DML]"
        [[ -f "$ver/dql.cypher" ]] && status="${status}[DQL]"
        echo "$ver $status"
    done
}

# メイン処理
case "${1:-usage}" in
    load)
        if [[ ! "$2" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "Error: Invalid version format. Use MAJOR.MINOR.PATCH"
            usage
        fi
        load_until_version "$2"
        ;;
    verify)
        if [[ ! "$2" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "Error: Invalid version format. Use MAJOR.MINOR.PATCH"
            usage
        fi
        verify_version "$2"
        ;;
    timeline)
        show_timeline
        ;;
    clean)
        rm -rf "$DB"
        echo "Database cleaned"
        ;;
    list)
        list_versions
        ;;
    *)
        usage
        ;;
esac