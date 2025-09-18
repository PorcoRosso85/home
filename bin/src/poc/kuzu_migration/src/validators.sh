#!/usr/bin/env bash
# Validators - Single responsibility: validate one thing and return status
# Following normalization principles - each validator does ONE thing

set -euo pipefail

# Validate DDL directory exists
validate_ddl_directory() {
    local ddl_dir="$1"
    [[ -d "$ddl_dir" ]]
}

# Validate migrations subdirectory exists
validate_migrations_directory() {
    local ddl_dir="$1"
    [[ -d "$ddl_dir/migrations" ]]
}

# Validate snapshots subdirectory exists
validate_snapshots_directory() {
    local ddl_dir="$1"
    [[ -d "$ddl_dir/snapshots" ]]
}

# Validate migration file naming convention
validate_migration_filename() {
    local filename="$1"
    [[ "$filename" =~ ^[0-9]{3}_[a-z0-9_]+\.cypher$ ]]
}

# Validate KuzuDB CLI is available
validate_kuzu_cli() {
    command -v kuzu &> /dev/null
}

# Validate database path is writable
validate_database_writable() {
    local db_path="$1"
    local db_dir
    db_dir=$(dirname "$db_path")
    
    # Check if parent directory is writable
    [[ -w "$db_dir" ]] || [[ ! -e "$db_dir" ]]
}

# Validate migration has not been applied
validate_migration_not_applied() {
    local db_path="$1"
    local migration_name="$2"
    
    # Check if migration exists in history
    local result
    result=$(kuzu "$db_path" -c "MATCH (m:_migration_history) WHERE m.migration_name = '$migration_name' RETURN count(m)" 2>/dev/null | tail -n 1)
    
    [[ "$result" == "0" ]]
}

# Validate Cypher syntax (basic check)
validate_cypher_syntax() {
    local file_path="$1"
    
    # Basic syntax checks
    local content
    content=$(cat "$file_path")
    
    # Check for unclosed quotes
    local single_quotes
    single_quotes=$(echo "$content" | tr -cd "'" | wc -c)
    [[ $((single_quotes % 2)) -eq 0 ]] || return 1
    
    # Check for unclosed parentheses
    local open_parens
    local close_parens
    open_parens=$(echo "$content" | tr -cd "(" | wc -c)
    close_parens=$(echo "$content" | tr -cd ")" | wc -c)
    [[ "$open_parens" -eq "$close_parens" ]] || return 1
    
    # Check for semicolon at end of non-comment lines
    echo "$content" | grep -v "^--" | grep -v "^$" | grep -q ";$" || return 1
    
    return 0
}

# Export all validators
export -f validate_ddl_directory
export -f validate_migrations_directory
export -f validate_snapshots_directory
export -f validate_migration_filename
export -f validate_kuzu_cli
export -f validate_database_writable
export -f validate_migration_not_applied
export -f validate_cypher_syntax