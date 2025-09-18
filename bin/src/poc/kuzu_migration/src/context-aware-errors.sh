#!/usr/bin/env bash
# Context-aware error handling that analyzes the actual state
# Not static messages, but dynamic analysis

set -euo pipefail

# Analyze DDL directory state and provide specific guidance
analyze_ddl_problem() {
    local expected_ddl="$1"
    local current_dir=$(pwd)
    
    # Don't just say "not found", analyze WHY
    if [[ -d "$expected_ddl" ]]; then
        # Directory exists, check structure
        local has_migrations=false
        local has_snapshots=false
        [[ -d "$expected_ddl/migrations" ]] && has_migrations=true
        [[ -d "$expected_ddl/snapshots" ]] && has_snapshots=true
        
        if ! $has_migrations || ! $has_snapshots; then
            echo "❌ Incomplete DDL structure"
            echo "Found: $expected_ddl"
            $has_migrations || echo "  Missing: migrations/"
            $has_snapshots || echo "  Missing: snapshots/"
            echo ""
            echo "Run: kuzu-migrate --ddl $expected_ddl init"
            return 1
        fi
        return 0
    fi
    
    # Check for common DDL locations
    local found_ddls=()
    for loc in ./ddl ./database/ddl ./db/ddl ../ddl; do
        [[ -d "$loc" ]] && found_ddls+=("$loc")
    done
    
    if [[ ${#found_ddls[@]} -gt 0 ]]; then
        echo "❌ DDL not at expected location: $expected_ddl"
        echo ""
        echo "Found DDL directories at:"
        for ddl in "${found_ddls[@]}"; do
            echo "  • $ddl"
        done
        echo ""
        echo "Use: kuzu-migrate --ddl ${found_ddls[0]} apply"
        return 1
    fi
    
    # Check if we're in wrong directory
    local project_markers=("flake.nix" "package.json" "Cargo.toml" "go.mod")
    local parent_has_project=false
    for marker in "${project_markers[@]}"; do
        [[ -f "../$marker" ]] && parent_has_project=true
    done
    
    if $parent_has_project; then
        echo "❌ Seems like you're in a subdirectory"
        echo "Current: $current_dir"
        echo ""
        echo "Try: cd .. && kuzu-migrate apply"
        return 1
    fi
    
    # No DDL found anywhere
    echo "❌ No DDL directory found"
    echo ""
    echo "Initialize: kuzu-migrate --ddl $expected_ddl init"
    return 1
}

# Analyze migration errors with actual file content
analyze_migration_error() {
    local migration_file="$1"
    local error_output="$2"
    
    # Read actual file content
    local content=$(cat "$migration_file" 2>/dev/null || echo "")
    
    # Pattern matching on actual error
    if [[ "$error_output" =~ "SyntaxError" ]]; then
        # Extract line number if available
        local line_num=$(echo "$error_output" | grep -oE 'line [0-9]+' | grep -oE '[0-9]+' || echo "")
        
        if [[ -n "$line_num" ]]; then
            echo "❌ Syntax error at line $line_num:"
            echo ""
            # Show context around error
            sed -n "$((line_num-2)),$((line_num+2))p" "$migration_file" | nl -v $((line_num-2))
            echo ""
        fi
    fi
    
    # Check for common patterns
    if ! grep -q ';[[:space:]]*$' "$migration_file"; then
        echo "💡 Missing semicolon at end of statement?"
    fi
    
    local open_parens=$(grep -o '(' "$migration_file" | wc -l)
    local close_parens=$(grep -o ')' "$migration_file" | wc -l)
    if [[ $open_parens -ne $close_parens ]]; then
        echo "💡 Unmatched parentheses: ( = $open_parens, ) = $close_parens"
    fi
}

# Export functions
export -f analyze_ddl_problem
export -f analyze_migration_error