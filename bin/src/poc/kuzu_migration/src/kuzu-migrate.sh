#!/usr/bin/env bash
set -euo pipefail

# kuzu-migrate - DDL directory management for KuzuDB migrations
VERSION="0.1.0"

# Default values
DDL_DIR=""
COMMAND=""
DB_PATH="${KUZU_DB_PATH:-./data/kuzu.db}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

show_usage() {
    cat << EOF
kuzu-migrate v${VERSION} - Manage your KuzuDB schema migrations

USAGE:
    kuzu-migrate [OPTIONS] COMMAND

COMMANDS:
    init        Create the DDL directory structure for migrations
    apply       Execute pending migrations to update your database
    status      Check which migrations are applied, pending, or failed
    validate    Check migration syntax without executing
    snapshot    Export the current database state for backup/rollback
    rollback    Restore database from a previous snapshot (coming soon)
    check       Show migration system status and environment
    diff        Compare schemas between two databases

OPTIONS:
    --ddl DIR   Path to DDL directory (default: ./ddl)
    --db PATH   Path to KuzuDB database (default: ${DB_PATH})
    --help      Show this help message
    --version   Show version information

APPLY OPTIONS:
    --dry-run   Show what would be applied without making changes

DIFF OPTIONS:
    --target PATH   Path to target database for comparison (required)

GETTING STARTED:
    # First time? Initialize your migration directory:
    kuzu-migrate init

    # Create your schema in ./ddl/migrations/000_initial.cypher, then:
    kuzu-migrate validate

    # If validation passes, apply the migrations:
    kuzu-migrate apply

    # Or see what would be applied without making changes:
    kuzu-migrate apply --dry-run

    # Check what's been applied:
    kuzu-migrate status

For more examples and documentation, visit:
https://github.com/kuzudb/kuzu

EOF
}

error() {
    echo -e "${RED}❌ ERROR: $1${NC}" >&2
    echo "" >&2
    echo "$2" >&2
    exit 1
}

error_with_hint() {
    local message="$1"
    local hint="$2"
    echo -e "${RED}❌ $message${NC}" >&2
    echo -e "→ $hint" >&2
    echo "" >&2
    echo "Run 'kuzu-migrate --help' for usage information" >&2
    exit 1
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

init_command() {
    local ddl_dir="$1"
    
    # Check if directory already exists
    if [[ -d "$ddl_dir" ]]; then
        info "DDL directory already exists at $ddl_dir"
        info "Checking for required subdirectories..."
    else
        info "Creating new DDL directory at $ddl_dir"
        mkdir -p "$ddl_dir"
    fi
    
    # Create required subdirectories
    local migrations_dir="$ddl_dir/migrations"
    local snapshots_dir="$ddl_dir/snapshots"
    
    # Create migrations directory
    if [[ ! -d "$migrations_dir" ]]; then
        mkdir -p "$migrations_dir"
        success "Created migrations directory: $migrations_dir"
    else
        info "Migrations directory already exists"
    fi
    
    # Create snapshots directory
    if [[ ! -d "$snapshots_dir" ]]; then
        mkdir -p "$snapshots_dir"
        success "Created snapshots directory: $snapshots_dir"
    else
        info "Snapshots directory already exists"
    fi
    
    # Create initial migration template
    local initial_migration="$migrations_dir/000_initial.cypher"
    if [[ ! -f "$initial_migration" ]]; then
        cat > "$initial_migration" << 'EOF'
-- Initial migration template
-- This file establishes the starting point for your database schema
-- 
-- Naming convention: NNN_description.cypher
--   - NNN: 3-digit sequence number (000-999)
--   - description: snake_case description of the migration
--
-- Example migrations:
--   001_create_user_nodes.cypher
--   002_add_friend_relationships.cypher
--   003_create_post_nodes.cypher

-- Create your initial schema here
-- Example:
-- CREATE NODE TABLE User (
--     id STRING PRIMARY KEY,
--     name STRING NOT NULL,
--     email STRING UNIQUE,
--     created_at TIMESTAMP DEFAULT now()
-- );

-- CREATE REL TABLE Follows (
--     FROM User TO User,
--     followed_at TIMESTAMP DEFAULT now()
-- );
EOF
        success "Created initial migration template: $initial_migration"
        echo ""
        info "Next steps:"
        echo "  1. Edit $initial_migration to define your initial schema"
        echo "  2. Run 'kuzu-migrate apply' to apply the migration"
        echo "  3. Create new migrations as needed (001_*.cypher, 002_*.cypher, etc.)"
    else
        info "Initial migration template already exists"
    fi
    
    # Summary
    echo ""
    success "Migration directory initialized successfully!"
    echo ""
    echo "Directory structure:"
    echo "  $ddl_dir/"
    echo "  ├── migrations/     # Your migration files go here"
    echo "  │   └── 000_initial.cypher"
    echo "  └── snapshots/      # Database snapshots will be stored here"
    echo ""
    info "Ready to start managing your KuzuDB migrations!"
}

apply_command() {
    local ddl_dir="$1"
    local db_path="$2"
    local dry_run="${3:-false}"
    
    # Check if DDL directory exists
    if [[ ! -d "$ddl_dir" ]]; then
        error_with_hint "DDL directory not found: $ddl_dir" "run 'init'"
    fi
    
    # Check if migrations directory exists
    local migrations_dir="$ddl_dir/migrations"
    if [[ ! -d "$migrations_dir" ]]; then
        error_with_hint "Migrations directory not found: $migrations_dir" "run 'init'"
    fi
    
    # Check if kuzu CLI is available
    if ! command -v kuzu &> /dev/null; then
        error_with_hint "command not found: kuzu" "check PATH"
    fi
    
    # Create database directory if it doesn't exist
    local db_dir
    db_dir=$(dirname "$db_path")
    if [[ ! -d "$db_dir" ]]; then
        info "Creating database directory: $db_dir"
        mkdir -p "$db_dir"
    fi
    
    # Initialize database if needed and create migration history table
    info "Initializing migration tracking..."
    local init_script
    init_script=$(mktemp)
    cat > "$init_script" << 'EOF'
-- Create migration history table if it doesn't exist
CREATE NODE TABLE IF NOT EXISTS _migration_history (
    migration_name STRING PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT now(),
    checksum STRING,
    execution_time_ms INT64,
    success BOOLEAN DEFAULT true,
    error_message STRING DEFAULT ''
);
EOF
    
    # Execute initialization
    if ! kuzu "$db_path" < "$init_script" > /dev/null 2>&1; then
        rm -f "$init_script"
        error_with_hint "Failed to initialize migration tracking table" "check database"
    fi
    rm -f "$init_script"
    
    # Find all .cypher files sorted by name
    info "Scanning for migration files..."
    local migration_files=()
    while IFS= read -r -d '' file; do
        migration_files+=("$file")
    done < <(find "$migrations_dir" -name "*.cypher" -type f -print0 | sort -z)
    
    if [[ ${#migration_files[@]} -eq 0 ]]; then
        info "No migration files found in $migrations_dir"
        return 0
    fi
    
    info "Found ${#migration_files[@]} migration file(s)"
    echo ""
    
    # Process each migration
    local applied_count=0
    local skipped_count=0
    local failed_count=0
    
    for migration_file in "${migration_files[@]}"; do
        local migration_name
        migration_name=$(basename "$migration_file")
        
        # Check if migration has already been applied
        local check_query="MATCH (m:_migration_history) WHERE m.migration_name = '$migration_name' RETURN m.migration_name;"
        local check_result
        check_result=$(echo "$check_query" | kuzu "$db_path" 2>/dev/null | grep -v "migration_name" | grep -v "^-" | grep -v "^$" || true)
        
        if [[ -n "$check_result" ]]; then
            info "⏭️  Skipping already applied migration: $migration_name"
            ((skipped_count++))
            continue
        fi
        
        # Calculate checksum of the migration file
        local checksum
        checksum=$(sha256sum "$migration_file" | cut -d' ' -f1)
        
        if [[ "$dry_run" == "true" ]]; then
            info "📄 [DRY-RUN] Would apply migration: $migration_name"
        else
            info "📄 Applying migration: $migration_name"
        fi
        
        # Record start time
        local start_time
        start_time=$(date +%s%3N)
        
        # Execute the migration
        local error_msg=""
        local migration_success=false
        
        if [[ "$dry_run" == "true" ]]; then
            # Create a transaction script that rolls back
            local dry_run_script
            dry_run_script=$(mktemp)
            
            # Wrap migration in transaction with rollback
            {
                echo "BEGIN TRANSACTION;"
                cat "$migration_file"
                echo "ROLLBACK;"
            } > "$dry_run_script"
            
            if kuzu "$db_path" < "$dry_run_script" > /dev/null 2>&1; then
                migration_success=true
            else
                error_msg=$(kuzu "$db_path" < "$dry_run_script" 2>&1 || true)
            fi
            
            rm -f "$dry_run_script"
        else
            # Normal execution
            if kuzu "$db_path" < "$migration_file" > /dev/null 2>&1; then
                migration_success=true
            else
                error_msg=$(kuzu "$db_path" < "$migration_file" 2>&1 || true)
            fi
        fi
        
        if [[ "$migration_success" == "true" ]]; then
            # Calculate execution time
            local end_time
            end_time=$(date +%s%3N)
            local exec_time=$((end_time - start_time))
            
            if [[ "$dry_run" == "true" ]]; then
                success "  ✅ [DRY-RUN] Would apply successfully (${exec_time}ms)"
                ((applied_count++))
            else
                # Record successful migration
                local record_query="CREATE (m:_migration_history {migration_name: '$migration_name', checksum: '$checksum', execution_time_ms: $exec_time});"
                if echo "$record_query" | kuzu "$db_path" > /dev/null 2>&1; then
                    success "  ✅ Applied successfully (${exec_time}ms)"
                    ((applied_count++))
                else
                    error_with_hint "Failed to record migration in history" "check database"
                fi
            fi
        else
            # Capture error output was already captured above
            error_msg=$(echo "$error_msg" | tr '\n' ' ' | sed "s/'/''/g")
            
            if [[ "$dry_run" == "true" ]]; then
                echo -e "${RED}  ❌ [DRY-RUN] Would fail to apply${NC}"
                echo -e "${RED}     Error: ${error_msg}${NC}"
            else
                # Record failed migration
                local record_query="CREATE (m:_migration_history {migration_name: '$migration_name', checksum: '$checksum', execution_time_ms: 0, success: false, error_message: '$error_msg'});"
                echo "$record_query" | kuzu "$db_path" > /dev/null 2>&1 || true
                
                echo -e "${RED}  ❌ Failed to apply${NC}"
                echo -e "${RED}     Error: ${error_msg}${NC}"
            fi
            
            ((failed_count++))
            
            # Stop on first failure
            break
        fi
    done
    
    # Summary
    echo ""
    if [[ "$dry_run" == "true" ]]; then
        echo "[DRY-RUN] Migration Summary:"
    else
        echo "Migration Summary:"
    fi
    echo "  📊 Total migrations: ${#migration_files[@]}"
    if [[ $applied_count -gt 0 ]]; then
        if [[ "$dry_run" == "true" ]]; then
            success "  ✅ Would apply: $applied_count"
        else
            success "  ✅ Applied: $applied_count"
        fi
    fi
    if [[ $skipped_count -gt 0 ]]; then
        info "  ⏭️  Skipped: $skipped_count (already applied)"
    fi
    if [[ $failed_count -gt 0 ]]; then
        if [[ "$dry_run" == "true" ]]; then
            echo -e "${RED}  ❌ Would fail: $failed_count${NC}"
        else
            echo -e "${RED}  ❌ Failed: $failed_count${NC}"
        fi
        echo ""
        if [[ "$dry_run" == "true" ]]; then
            error_with_hint "Some migrations would fail" "fix migration before applying"
        else
            error_with_hint "Migration process halted due to failure" "fix migration"
        fi
    fi
    
    if [[ $applied_count -gt 0 && $failed_count -eq 0 ]]; then
        echo ""
        if [[ "$dry_run" == "true" ]]; then
            success "All pending migrations would apply successfully!"
            echo ""
            info "Run without --dry-run to actually apply these migrations"
        else
            success "All pending migrations applied successfully!"
        fi
    elif [[ $applied_count -eq 0 && $skipped_count -gt 0 && $failed_count -eq 0 ]]; then
        echo ""
        info "Database is already up to date!"
    fi
}

status_command() {
    local ddl_dir="$1"
    local db_path="$2"
    
    # Check if DDL directory exists
    if [[ ! -d "$ddl_dir" ]]; then
        error_with_hint "DDL directory not found: $ddl_dir" "run 'init'"
    fi
    
    # Check if database exists
    if [[ ! -d "$db_path" ]]; then
        info "Database not found at: $db_path"
        info "No migrations have been applied yet."
        return 0
    fi
    
    # Check if kuzu CLI is available
    if ! command -v kuzu &> /dev/null; then
        error_with_hint "command not found: kuzu" "check PATH"
    fi
    
    echo "=== Migration Status ==="
    echo ""
    
    # Check if migration history table exists
    local check_table_query="CALL TABLE_INFO('_migration_history') RETURN *;"
    if ! echo "$check_table_query" | kuzu "$db_path" > /dev/null 2>&1; then
        info "Migration history table not found. No migrations have been applied yet."
        echo ""
        
        # Show available migrations
        local migrations_dir="$ddl_dir/migrations"
        if [[ -d "$migrations_dir" ]]; then
            local migration_files=()
            while IFS= read -r -d '' file; do
                migration_files+=("$file")
            done < <(find "$migrations_dir" -name "*.cypher" -type f -print0 | sort -z)
            
            if [[ ${#migration_files[@]} -gt 0 ]]; then
                echo "📁 Available migrations (not yet applied):"
                for file in "${migration_files[@]}"; do
                    echo "   - $(basename "$file")"
                done
            fi
        fi
        return 0
    fi
    
    # Get applied migrations
    echo "✅ Applied migrations:"
    local applied_query="MATCH (m:_migration_history) WHERE m.success = true RETURN m.migration_name, m.applied_at, m.execution_time_ms ORDER BY m.applied_at;"
    local applied_output
    applied_output=$(echo "$applied_query" | kuzu "$db_path" 2>/dev/null || true)
    
    # Parse and display applied migrations
    local has_applied=false
    while IFS= read -r line; do
        # Skip header lines and empty lines
        if [[ "$line" =~ ^migration_name ]] || [[ "$line" =~ ^-+ ]] || [[ -z "$line" ]]; then
            continue
        fi
        
        # Parse the output (format: migration_name|applied_at|execution_time_ms)
        if [[ "$line" =~ \| ]]; then
            has_applied=true
            local migration_name
            migration_name=$(echo "$line" | cut -d'|' -f1 | xargs)
            local applied_at
            applied_at=$(echo "$line" | cut -d'|' -f2 | xargs)
            local exec_time
            exec_time=$(echo "$line" | cut -d'|' -f3 | xargs)
            echo "   ✓ $migration_name (applied: $applied_at, took: ${exec_time}ms)"
        fi
    done <<< "$applied_output"
    
    if [[ "$has_applied" == "false" ]]; then
        echo "   (none)"
    fi
    echo ""
    
    # Get failed migrations
    local failed_query="MATCH (m:_migration_history) WHERE m.success = false RETURN m.migration_name, m.applied_at, m.error_message ORDER BY m.applied_at;"
    local failed_output
    failed_output=$(echo "$failed_query" | kuzu "$db_path" 2>/dev/null || true)
    
    local has_failed=false
    while IFS= read -r line; do
        if [[ "$line" =~ ^migration_name ]] || [[ "$line" =~ ^-+ ]] || [[ -z "$line" ]]; then
            continue
        fi
        
        if [[ "$line" =~ \| ]]; then
            if [[ "$has_failed" == "false" ]]; then
                echo "❌ Failed migrations:"
                has_failed=true
            fi
            local migration_name
            migration_name=$(echo "$line" | cut -d'|' -f1 | xargs)
            local applied_at
            applied_at=$(echo "$line" | cut -d'|' -f2 | xargs)
            local error_msg
            error_msg=$(echo "$line" | cut -d'|' -f3 | xargs)
            echo "   ✗ $migration_name (attempted: $applied_at)"
            echo "     Error: $error_msg"
        fi
    done <<< "$failed_output"
    
    if [[ "$has_failed" == "true" ]]; then
        echo ""
    fi
    
    # Find pending migrations
    local migrations_dir="$ddl_dir/migrations"
    if [[ -d "$migrations_dir" ]]; then
        local migration_files=()
        while IFS= read -r -d '' file; do
            migration_files+=("$file")
        done < <(find "$migrations_dir" -name "*.cypher" -type f -print0 | sort -z)
        
        if [[ ${#migration_files[@]} -gt 0 ]]; then
            # Get list of applied migrations
            local applied_list
            applied_list=$(echo "MATCH (m:_migration_history) RETURN m.migration_name;" | kuzu "$db_path" 2>/dev/null | grep -v "migration_name" | grep -v "^-" | grep -v "^$" || true)
            
            local pending_count=0
            local pending_files=()
            for file in "${migration_files[@]}"; do
                local migration_name
                migration_name=$(basename "$file")
                if ! echo "$applied_list" | grep -q "^$migration_name$"; then
                    pending_files+=("$migration_name")
                    ((pending_count++))
                fi
            done
            
            if [[ $pending_count -gt 0 ]]; then
                echo "📄 Pending migrations:"
                for file in "${pending_files[@]}"; do
                    echo "   - $file"
                done
                echo ""
            fi
        fi
    fi
    
    # Get database version (last applied migration)
    local version_query="MATCH (m:_migration_history) WHERE m.success = true RETURN m.migration_name ORDER BY m.applied_at DESC LIMIT 1;"
    local current_version
    current_version=$(echo "$version_query" | kuzu "$db_path" 2>/dev/null | grep -v "migration_name" | grep -v "^-" | grep -v "^$" | xargs || true)
    
    if [[ -n "$current_version" ]]; then
        success "Current database version: $current_version"
    else
        info "Database version: No migrations applied"
    fi
}

snapshot_command() {
    local ddl_dir="$1"
    local db_path="$2"
    shift 2
    
    # Parse snapshot-specific arguments
    local version_tag=""
    while [[ $# -gt 0 ]]; do
        case $1 in
            --version)
                version_tag="$2"
                shift 2
                ;;
            *)
                error_with_hint "Unknown snapshot option: $1" "see --help"
                ;;
        esac
    done
    
    # Check if DDL directory exists
    if [[ ! -d "$ddl_dir" ]]; then
        error_with_hint "DDL directory not found: $ddl_dir" "run 'init'"
    fi
    
    # Check if database exists
    if [[ ! -d "$db_path" ]]; then
        error_with_hint "Database not found at: $db_path" "run 'apply' first"
    fi
    
    # Check if kuzu CLI is available
    if ! command -v kuzu &> /dev/null; then
        error_with_hint "command not found: kuzu" "check PATH"
    fi
    
    # Determine snapshot directory name
    local snapshots_dir="$ddl_dir/snapshots"
    local snapshot_name
    if [[ -n "$version_tag" ]]; then
        # Validate version tag format (e.g., v1.0.0)
        if [[ ! "$version_tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            error_with_hint "Invalid version format: $version_tag" "use vX.Y.Z"
        fi
        snapshot_name="$version_tag"
    else
        # Use timestamp-based name
        snapshot_name="snapshot_$(date +%Y%m%d_%H%M%S)"
    fi
    
    local snapshot_path="$snapshots_dir/$snapshot_name"
    
    # Check if snapshot already exists
    if [[ -d "$snapshot_path" ]]; then
        error_with_hint "Snapshot already exists: $snapshot_name" "use different version"
    fi
    
    # Create snapshot directory
    info "Creating snapshot: $snapshot_name"
    mkdir -p "$snapshot_path"
    
    # Export database
    info "Exporting database..."
    local export_query="EXPORT DATABASE '$snapshot_path';"
    
    if echo "$export_query" | kuzu "$db_path" > /dev/null 2>&1; then
        success "Database exported successfully!"
    else
        # Clean up failed snapshot directory
        rm -rf "$snapshot_path"
        error_with_hint "Failed to export database" "check permissions"
    fi
    
    # Create snapshot metadata
    local metadata_file="$snapshot_path/snapshot_metadata.json"
    local current_version
    current_version=$(echo "MATCH (m:_migration_history) WHERE m.success = true RETURN m.migration_name ORDER BY m.applied_at DESC LIMIT 1;" | kuzu "$db_path" 2>/dev/null | grep -v "migration_name" | grep -v "^-" | grep -v "^$" | xargs || echo "none")
    
    cat > "$metadata_file" << EOF
{
    "snapshot_name": "$snapshot_name",
    "created_at": "$(date -Iseconds)",
    "database_path": "$db_path",
    "last_migration": "$current_version",
    "kuzu_version": "$(kuzu --version 2>/dev/null || echo 'unknown')"
}
EOF
    
    # List exported files
    echo ""
    echo "📦 Snapshot created at: $snapshot_path"
    echo ""
    echo "Exported contents:"
    
    # Show directory structure
    if command -v tree &> /dev/null; then
        tree -L 2 "$snapshot_path" | tail -n +2
    else
        find "$snapshot_path" -type f -o -type d | sort | while read -r item; do
            local relative_path="${item#"$snapshot_path"/}"
            if [[ -z "$relative_path" ]]; then
                continue
            fi
            
            local depth
            depth=$(echo "$relative_path" | grep -o "/" | wc -l)
            local indent=""
            for ((i=0; i<depth; i++)); do
                indent="  $indent"
            done
            
            local basename
            basename=$(basename "$item")
            if [[ -d "$item" ]]; then
                echo "${indent}├── $basename/"
            else
                echo "${indent}├── $basename"
            fi
        done
    fi
    
    echo ""
    success "Snapshot completed successfully!"
    
    # Show how to restore
    echo ""
    info "To restore from this snapshot:"
    echo "  kuzu-migrate rollback --snapshot $snapshot_name"
}

validate_command() {
    local ddl_dir="$1"
    local db_path="$2"
    
    # Check if DDL directory exists
    if [[ ! -d "$ddl_dir" ]]; then
        error_with_hint "DDL directory not found: $ddl_dir" "run 'init'"
    fi
    
    # Check if migrations directory exists
    local migrations_dir="$ddl_dir/migrations"
    if [[ ! -d "$migrations_dir" ]]; then
        error_with_hint "Migrations directory not found: $migrations_dir" "run 'init'"
    fi
    
    # Check if kuzu CLI is available
    if ! command -v kuzu &> /dev/null; then
        error_with_hint "command not found: kuzu" "check PATH"
    fi
    
    echo "=== Migration Validation ==="
    echo ""
    
    # Find all .cypher files sorted by name
    info "Scanning for migration files..."
    local migration_files=()
    while IFS= read -r -d '' file; do
        migration_files+=("$file")
    done < <(find "$migrations_dir" -name "*.cypher" -type f -print0 | sort -z)
    
    if [[ ${#migration_files[@]} -eq 0 ]]; then
        info "No migration files found in $migrations_dir"
        return 0
    fi
    
    info "Found ${#migration_files[@]} migration file(s)"
    echo ""
    
    # Create temporary database for validation
    local temp_db_dir
    temp_db_dir=$(mktemp -d)
    local temp_db_path="$temp_db_dir/validation.db"
    
    # Initialize temporary database
    local init_script
    init_script=$(mktemp)
    cat > "$init_script" << 'EOF'
-- Minimal initialization for validation
CREATE NODE TABLE IF NOT EXISTS _validation_test (id INT64 PRIMARY KEY);
EOF
    
    if ! kuzu "$temp_db_path" < "$init_script" > /dev/null 2>&1; then
        rm -f "$init_script"
        rm -rf "$temp_db_dir"
        error_with_hint "Failed to create temporary database for validation" "check permissions"
    fi
    rm -f "$init_script"
    
    # Process each migration for syntax validation
    local valid_count=0
    local invalid_count=0
    local validation_failed=false
    
    for migration_file in "${migration_files[@]}"; do
        local migration_name
        migration_name=$(basename "$migration_file")
        
        info "🔍 Validating: $migration_name"
        
        # Create validation script with EXPLAIN prefix
        local validation_script
        validation_script=$(mktemp)
        
        # Read migration file and prefix each non-comment line with EXPLAIN
        while IFS= read -r line || [[ -n "$line" ]]; do
            # Skip empty lines and comments
            if [[ -z "$line" || "$line" =~ ^[[:space:]]*-- ]]; then
                continue
            fi
            
            # Skip lines that are only whitespace
            if [[ "$line" =~ ^[[:space:]]*$ ]]; then
                continue
            fi
            
            # Add EXPLAIN prefix to each DDL statement
            echo "EXPLAIN $line" >> "$validation_script"
        done < "$migration_file"
        
        # Execute validation
        local error_msg=""
        if kuzu "$temp_db_path" < "$validation_script" > /dev/null 2>&1; then
            success "  ✅ Syntax validation passed"
            ((valid_count++))
        else
            # Capture error output for detailed feedback
            error_msg=$(kuzu "$temp_db_path" < "$validation_script" 2>&1 | head -5 | tr '\n' ' ' || true)
            echo -e "${RED}  ❌ Syntax validation failed${NC}"
            echo -e "${RED}     Error: ${error_msg}${NC}"
            ((invalid_count++))
            validation_failed=true
        fi
        
        # Clean up validation script
        rm -f "$validation_script"
    done
    
    # Clean up temporary database
    rm -rf "$temp_db_dir"
    
    # Summary
    echo ""
    echo "=== Validation Summary ==="
    echo "  📊 Total migrations: ${#migration_files[@]}"
    if [[ $valid_count -gt 0 ]]; then
        success "  ✅ Valid: $valid_count"
    fi
    if [[ $invalid_count -gt 0 ]]; then
        echo -e "${RED}  ❌ Invalid: $invalid_count${NC}"
    fi
    
    echo ""
    if [[ $validation_failed == true ]]; then
        error_with_hint "Migration validation failed" "fix syntax errors"
    else
        success "All migration files have valid syntax!"
    fi
}

check_command() {
    local ddl_dir="$1"
    local db_path="$2"
    
    echo "=== Migration System Check ==="
    echo ""
    
    # Check DDL directory
    echo "📁 DDL Directory:"
    if [[ -d "$ddl_dir" ]]; then
        echo "   ✓ Exists: $ddl_dir"
        
        # Check migrations subdirectory
        local migrations_dir="$ddl_dir/migrations"
        if [[ -d "$migrations_dir" ]]; then
            local migration_count
            migration_count=$(find "$migrations_dir" -name "*.cypher" -type f 2>/dev/null | wc -l)
            echo "   ✓ Migrations directory: $migration_count file(s)"
        else
            echo "   ✗ Migrations directory: not found"
            echo "     → run 'kuzu-migrate init' to create"
        fi
        
        # Check snapshots subdirectory
        local snapshots_dir="$ddl_dir/snapshots"
        if [[ -d "$snapshots_dir" ]]; then
            local snapshot_count
            snapshot_count=$(find "$snapshots_dir" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
            echo "   ✓ Snapshots directory: $snapshot_count snapshot(s)"
        else
            echo "   ✗ Snapshots directory: not found"
            echo "     → run 'kuzu-migrate init' to create"
        fi
    else
        echo "   ✗ Not found: $ddl_dir"
        echo "     → run 'kuzu-migrate init' to create"
    fi
    
    echo ""
    
    # Check environment
    echo "🔧 Environment:"
    
    # Check kuzu CLI
    if command -v kuzu &> /dev/null; then
        local kuzu_version
        kuzu_version=$(kuzu --version 2>/dev/null || echo "unknown")
        echo "   ✓ KuzuDB CLI: available (version: $kuzu_version)"
    else
        echo "   ✗ KuzuDB CLI: not found in PATH"
        echo "     → ensure 'kuzu' is installed and in PATH"
    fi
    
    # Check database path
    echo "   ℹ Database path: $db_path"
    if [[ -d "$db_path" ]]; then
        echo "   ✓ Database exists"
        
        # Check if we can connect
        if command -v kuzu &> /dev/null; then
            if echo "RETURN 'test';" | kuzu "$db_path" > /dev/null 2>&1; then
                echo "   ✓ Database connection: OK"
                
                # Check migration history table
                local check_table_query="CALL TABLE_INFO('_migration_history') RETURN *;"
                if echo "$check_table_query" | kuzu "$db_path" > /dev/null 2>&1; then
                    echo "   ✓ Migration tracking: initialized"
                else
                    echo "   ℹ Migration tracking: not initialized"
                    echo "     → will be created on first 'apply'"
                fi
            else
                echo "   ✗ Database connection: failed"
                echo "     → check database integrity"
            fi
        fi
    else
        echo "   ℹ Database not created yet"
        echo "     → will be created on first 'apply'"
    fi
    
    echo ""
    
    # Check migration files
    if [[ -d "$ddl_dir/migrations" ]]; then
        echo "📄 Migration Files:"
        local migration_files=()
        while IFS= read -r -d '' file; do
            migration_files+=("$file")
        done < <(find "$ddl_dir/migrations" -name "*.cypher" -type f -print0 | sort -z)
        
        if [[ ${#migration_files[@]} -gt 0 ]]; then
            for file in "${migration_files[@]}"; do
                local filename
                filename=$(basename "$file")
                local filesize
                filesize=$(stat -c %s "$file" 2>/dev/null || stat -f %z "$file" 2>/dev/null || echo "0")
                
                # Check naming convention
                if [[ "$filename" =~ ^[0-9]{3}_[a-z0-9_]+\.cypher$ ]]; then
                    echo "   ✓ $filename ($filesize bytes)"
                else
                    echo "   ⚠ $filename ($filesize bytes) - non-standard naming"
                    echo "     → use format: NNN_description.cypher"
                fi
            done
        else
            echo "   (none found)"
        fi
        
        echo ""
    fi
    
    # Summary
    echo "📊 Summary:"
    local issues=0
    
    if [[ ! -d "$ddl_dir" ]]; then
        echo "   ⚠ DDL directory not initialized"
        ((issues++))
    fi
    
    if ! command -v kuzu &> /dev/null; then
        echo "   ⚠ KuzuDB CLI not available"
        ((issues++))
    fi
    
    if [[ $issues -eq 0 ]]; then
        success "   ✅ System ready for migrations"
    else
        echo "   ⚠ $issues issue(s) found"
        echo ""
        info "Run 'kuzu-migrate --help' for usage information"
    fi
}

diff_command() {
    local db_path="$1"
    local target_path="$2"
    
    # Check if kuzu CLI is available
    if ! command -v kuzu &> /dev/null; then
        error_with_hint "command not found: kuzu" "check PATH"
    fi
    
    # Validate database paths
    if [[ ! -d "$db_path" ]]; then
        error_with_hint "Source database not found: $db_path" "check database path"
    fi
    
    if [[ ! -d "$target_path" ]]; then
        error_with_hint "Target database not found: $target_path" "check --target path"
    fi
    
    # Test connections
    if ! echo "RETURN 'test';" | kuzu "$db_path" > /dev/null 2>&1; then
        error_with_hint "Cannot connect to source database: $db_path" "check database integrity"
    fi
    
    if ! echo "RETURN 'test';" | kuzu "$target_path" > /dev/null 2>&1; then
        error_with_hint "Cannot connect to target database: $target_path" "check database integrity"
    fi
    
    echo "=== Database Schema Comparison ==="
    echo ""
    info "Source: $db_path"
    info "Target: $target_path"
    echo ""
    
    # Create temporary directories for schema exports
    local temp_dir
    temp_dir=$(mktemp -d)
    local source_schema_dir="$temp_dir/source"
    local target_schema_dir="$temp_dir/target"
    
    # Export schemas with schema_only=true
    info "Exporting source database schema..."
    local source_export="EXPORT DATABASE '$source_schema_dir' (schema_only=true);"
    if ! echo "$source_export" | kuzu "$db_path" > /dev/null 2>&1; then
        rm -rf "$temp_dir"
        error_with_hint "Failed to export source schema" "check permissions"
    fi
    
    info "Exporting target database schema..."
    local target_export="EXPORT DATABASE '$target_schema_dir' (schema_only=true);"
    if ! echo "$target_export" | kuzu "$target_path" > /dev/null 2>&1; then
        rm -rf "$temp_dir"
        error_with_hint "Failed to export target schema" "check permissions"
    fi
    
    # Find and compare schema files
    local source_schema_file="$source_schema_dir/schema.cypher"
    local target_schema_file="$target_schema_dir/schema.cypher"
    
    if [[ ! -f "$source_schema_file" ]]; then
        rm -rf "$temp_dir"
        error_with_hint "Source schema file not found" "check export output"
    fi
    
    if [[ ! -f "$target_schema_file" ]]; then
        rm -rf "$temp_dir"
        error_with_hint "Target schema file not found" "check export output"
    fi
    
    # Generate checksums
    local source_checksum
    local target_checksum
    source_checksum=$(sha256sum "$source_schema_file" | cut -d' ' -f1)
    target_checksum=$(sha256sum "$target_schema_file" | cut -d' ' -f1)
    
    echo "🔍 Schema Analysis:"
    echo "   Source checksum: $source_checksum"
    echo "   Target checksum: $target_checksum"
    echo ""
    
    if [[ "$source_checksum" == "$target_checksum" ]]; then
        success "✅ Schemas are identical"
        rm -rf "$temp_dir"
        return 0
    fi
    
    echo "📊 Schema Differences Found:"
    echo ""
    
    # Use diff to show detailed differences
    if command -v diff &> /dev/null; then
        echo "=== Detailed Schema Diff ==="
        echo ""
        
        # Create unified diff with labels
        if diff -u --label "Source ($db_path)" --label "Target ($target_path)" "$source_schema_file" "$target_schema_file" 2>/dev/null; then
            success "No differences detected by line comparison"
        else
            local diff_lines
            diff_lines=$(diff -u --label "Source ($db_path)" --label "Target ($target_path)" "$source_schema_file" "$target_schema_file" 2>/dev/null | wc -l)
            info "Diff output contains $diff_lines lines"
        fi
    else
        info "diff command not available, showing file statistics:"
        echo ""
        
        local source_lines target_lines
        source_lines=$(wc -l < "$source_schema_file")
        target_lines=$(wc -l < "$target_schema_file")
        
        echo "   Source schema: $source_lines lines"
        echo "   Target schema: $target_lines lines"
        
        if [[ $source_lines -gt $target_lines ]]; then
            echo "   → Source has $((source_lines - target_lines)) more lines"
        elif [[ $target_lines -gt $source_lines ]]; then
            echo "   → Target has $((target_lines - source_lines)) more lines"
        fi
    fi
    
    echo ""
    echo "=== Schema File Locations ==="
    info "Temporary schema exports saved at:"
    echo "   Source: $source_schema_file"
    echo "   Target: $target_schema_file"
    echo ""
    info "Use 'cat' or your preferred editor to examine the differences"
    echo "   cat '$source_schema_file'"
    echo "   cat '$target_schema_file'"
    echo ""
    info "Clean up temp files with: rm -rf '$temp_dir'"
    
    # Clean up automatically after showing paths
    # rm -rf "$temp_dir"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --ddl)
            DDL_DIR="$2"
            shift 2
            ;;
        --db)
            DB_PATH="$2"
            shift 2
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        --version|-v)
            echo "kuzu-migrate v${VERSION}"
            exit 0
            ;;
        init|apply|status|validate|snapshot|rollback|check|diff)
            COMMAND="$1"
            shift
            # Don't shift additional arguments for snapshot and diff commands
            break
            ;;
        *)
            error_with_hint "Unknown option: $1" "see --help"
            ;;
    esac
done

# Set default DDL directory if not specified
if [[ -z "$DDL_DIR" ]]; then
    DDL_DIR="${KUZU_DDL_DIR:-./ddl}"
fi

# Execute commands
case "$COMMAND" in
    init)
        init_command "$DDL_DIR"
        ;;
    apply)
        # Parse apply-specific arguments
        dry_run="false"
        while [[ $# -gt 0 ]]; do
            case $1 in
                --dry-run)
                    dry_run="true"
                    shift
                    ;;
                *)
                    error_with_hint "Unknown apply option: $1" "see --help"
                    ;;
            esac
        done
        apply_command "$DDL_DIR" "$DB_PATH" "$dry_run"
        ;;
    status)
        status_command "$DDL_DIR" "$DB_PATH"
        ;;
    validate)
        validate_command "$DDL_DIR" "$DB_PATH"
        ;;
    snapshot)
        snapshot_command "$DDL_DIR" "$DB_PATH" "$@"
        ;;
    rollback)
        info "Rollback command will be implemented in Step 2"
        ;;
    check)
        check_command "$DDL_DIR" "$DB_PATH"
        ;;
    diff)
        # Parse diff-specific arguments
        target_path=""
        while [[ $# -gt 0 ]]; do
            case $1 in
                --target)
                    target_path="$2"
                    shift 2
                    ;;
                *)
                    error_with_hint "Unknown diff option: $1" "see --help"
                    ;;
            esac
        done
        
        if [[ -z "$target_path" ]]; then
            error_with_hint "Missing --target option for diff command" "specify target database path"
        fi
        
        diff_command "$DB_PATH" "$target_path"
        ;;
    "")
        show_usage
        exit 1
        ;;
    *)
        error_with_hint "Unknown command: $COMMAND" "see --help"
        ;;
esac