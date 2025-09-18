#!/usr/bin/env bash
# Minimalist approach: errors show what IS, not what SHOULD BE
# Let users decide, don't prescribe solutions

set -euo pipefail

# Just report facts
report_state() {
    local context="$1"
    
    case "$context" in
        ddl-check)
            local ddl_dir="${2:-./ddl}"
            echo "DDL check: $ddl_dir"
            [[ -d "$ddl_dir" ]] && echo "  exists: yes" || echo "  exists: no"
            [[ -d "$ddl_dir/migrations" ]] && echo "  migrations/: yes" || echo "  migrations/: no"
            [[ -d "$ddl_dir/snapshots" ]] && echo "  snapshots/: yes" || echo "  snapshots/: no"
            
            # Show what we found, not what we expect
            if [[ -d "$ddl_dir" ]]; then
                echo "  contents:"
                find "$ddl_dir" -maxdepth 2 -type f -name "*.cypher" | head -5
            fi
            ;;
            
        migration-check)
            local file="$2"
            echo "Migration: $file"
            [[ -f "$file" ]] || { echo "  exists: no"; return; }
            
            echo "  size: $(wc -c < "$file") bytes"
            echo "  lines: $(wc -l < "$file")"
            echo "  semicolons: $(grep -o ';' "$file" | wc -l)"
            echo "  CREATE statements: $(grep -c 'CREATE' "$file" || echo 0)"
            echo "  ALTER statements: $(grep -c 'ALTER' "$file" || echo 0)"
            ;;
            
        environment-check)
            echo "Environment:"
            echo "  pwd: $(pwd)"
            echo "  kuzu: $(command -v kuzu || echo 'not found')"
            echo "  KUZU_DB_PATH: ${KUZU_DB_PATH:-not set}"
            echo "  KUZU_DDL_DIR: ${KUZU_DDL_DIR:-not set}"
            
            # Show neighboring directories
            echo "  nearby DDLs:"
            find . -maxdepth 3 -type d -name "ddl" 2>/dev/null | head -5
            ;;
    esac
}

# Minimal error - just facts
error_minimal() {
    local what="$1"
    local where="$2"
    
    echo "❌ $what"
    echo "   at: $where"
    
    # Add context without prescribing
    case "$what" in
        "directory not found")
            echo "   type: directory"
            echo "   exists: no"
            ;;
        "command not found")
            echo "   type: executable"
            echo "   in PATH: no"
            ;;
        "syntax error")
            echo "   type: cypher"
            echo "   valid: no"
            ;;
    esac
}

export -f report_state
export -f error_minimal