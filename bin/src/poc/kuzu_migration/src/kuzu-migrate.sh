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
kuzu-migrate v${VERSION} - KuzuDB Migration CLI

Usage:
    kuzu-migrate [OPTIONS] COMMAND

Commands:
    init        Initialize DDL directory structure
    apply       Apply pending migrations
    status      Show migration status
    snapshot    Create database snapshot
    rollback    Rollback to a snapshot

Options:
    --ddl DIR   Specify DDL directory (default: ./ddl)
    --db PATH   Database path (default: ${DB_PATH})
    --help      Show this help message
    --version   Show version

Environment Variables:
    KUZU_DDL_DIR    Default DDL directory
    KUZU_DB_PATH    Default database path

Examples:
    kuzu-migrate --ddl ./ddl init
    kuzu-migrate apply
    kuzu-migrate snapshot --version v1.0.0

EOF
}

error() {
    echo -e "${RED}❌ ERROR: $1${NC}" >&2
    echo "" >&2
    echo "$2" >&2
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
    
    # Check if DDL directory exists
    if [[ ! -d "$ddl_dir" ]]; then
        error "DDL directory not found: $ddl_dir" "Run 'kuzu-migrate init' first to create the DDL directory structure."
    fi
    
    # Check if migrations directory exists
    local migrations_dir="$ddl_dir/migrations"
    if [[ ! -d "$migrations_dir" ]]; then
        error "Migrations directory not found: $migrations_dir" "The DDL directory structure appears to be incomplete. Run 'kuzu-migrate init' to fix this."
    fi
    
    # Check if kuzu CLI is available
    if ! command -v kuzu &> /dev/null; then
        error "KuzuDB CLI not found" "Please install KuzuDB CLI first. Visit https://kuzudb.com for installation instructions."
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
        error "Failed to initialize migration tracking table" "Could not create _migration_history table in the database."
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
        
        info "📄 Applying migration: $migration_name"
        
        # Record start time
        local start_time
        start_time=$(date +%s%3N)
        
        # Execute the migration
        local error_msg=""
        if kuzu "$db_path" < "$migration_file" > /dev/null 2>&1; then
            # Calculate execution time
            local end_time
            end_time=$(date +%s%3N)
            local exec_time=$((end_time - start_time))
            
            # Record successful migration
            local record_query="CREATE (m:_migration_history {migration_name: '$migration_name', checksum: '$checksum', execution_time_ms: $exec_time});"
            if echo "$record_query" | kuzu "$db_path" > /dev/null 2>&1; then
                success "  ✅ Applied successfully (${exec_time}ms)"
                ((applied_count++))
            else
                error "Failed to record migration in history" "Could not save migration record for $migration_name"
            fi
        else
            # Capture error output
            error_msg=$(kuzu "$db_path" < "$migration_file" 2>&1 || true)
            error_msg=$(echo "$error_msg" | tr '\n' ' ' | sed "s/'/''/g")
            
            # Record failed migration
            local record_query="CREATE (m:_migration_history {migration_name: '$migration_name', checksum: '$checksum', execution_time_ms: 0, success: false, error_message: '$error_msg'});"
            echo "$record_query" | kuzu "$db_path" > /dev/null 2>&1 || true
            
            echo -e "${RED}  ❌ Failed to apply${NC}"
            echo -e "${RED}     Error: ${error_msg}${NC}"
            ((failed_count++))
            
            # Stop on first failure
            break
        fi
    done
    
    # Summary
    echo ""
    echo "Migration Summary:"
    echo "  📊 Total migrations: ${#migration_files[@]}"
    if [[ $applied_count -gt 0 ]]; then
        success "  ✅ Applied: $applied_count"
    fi
    if [[ $skipped_count -gt 0 ]]; then
        info "  ⏭️  Skipped: $skipped_count (already applied)"
    fi
    if [[ $failed_count -gt 0 ]]; then
        echo -e "${RED}  ❌ Failed: $failed_count${NC}"
        echo ""
        error "Migration process halted due to failure" "Fix the failing migration and run 'kuzu-migrate apply' again."
    fi
    
    if [[ $applied_count -gt 0 && $failed_count -eq 0 ]]; then
        echo ""
        success "All pending migrations applied successfully!"
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
        error "DDL directory not found: $ddl_dir" "Run 'kuzu-migrate init' first to create the DDL directory structure."
    fi
    
    # Check if database exists
    if [[ ! -d "$db_path" ]]; then
        info "Database not found at: $db_path"
        info "No migrations have been applied yet."
        return 0
    fi
    
    # Check if kuzu CLI is available
    if ! command -v kuzu &> /dev/null; then
        error "KuzuDB CLI not found" "Please install KuzuDB CLI first. Visit https://kuzudb.com for installation instructions."
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
                error "Unknown snapshot option: $1" "Run 'kuzu-migrate --help' for usage."
                ;;
        esac
    done
    
    # Check if DDL directory exists
    if [[ ! -d "$ddl_dir" ]]; then
        error "DDL directory not found: $ddl_dir" "Run 'kuzu-migrate init' first to create the DDL directory structure."
    fi
    
    # Check if database exists
    if [[ ! -d "$db_path" ]]; then
        error "Database not found at: $db_path" "No database to snapshot. Run 'kuzu-migrate apply' first to create the database."
    fi
    
    # Check if kuzu CLI is available
    if ! command -v kuzu &> /dev/null; then
        error "KuzuDB CLI not found" "Please install KuzuDB CLI first. Visit https://kuzudb.com for installation instructions."
    fi
    
    # Determine snapshot directory name
    local snapshots_dir="$ddl_dir/snapshots"
    local snapshot_name
    if [[ -n "$version_tag" ]]; then
        # Validate version tag format (e.g., v1.0.0)
        if [[ ! "$version_tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            error "Invalid version format: $version_tag" "Version should be in format vX.Y.Z (e.g., v1.0.0)"
        fi
        snapshot_name="$version_tag"
    else
        # Use timestamp-based name
        snapshot_name="snapshot_$(date +%Y%m%d_%H%M%S)"
    fi
    
    local snapshot_path="$snapshots_dir/$snapshot_name"
    
    # Check if snapshot already exists
    if [[ -d "$snapshot_path" ]]; then
        error "Snapshot already exists: $snapshot_name" "Choose a different version or let the system generate a timestamp-based name."
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
        error "Failed to export database" "Could not create snapshot. Check database permissions and disk space."
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
        init|apply|status|snapshot|rollback)
            COMMAND="$1"
            shift
            # Don't shift additional arguments for snapshot command
            break
            ;;
        *)
            error "Unknown option: $1" "Run 'kuzu-migrate --help' for usage."
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
        apply_command "$DDL_DIR" "$DB_PATH"
        ;;
    status)
        status_command "$DDL_DIR" "$DB_PATH"
        ;;
    snapshot)
        snapshot_command "$DDL_DIR" "$DB_PATH" "$@"
        ;;
    rollback)
        info "Rollback command will be implemented in Step 2"
        ;;
    "")
        error "No command specified" "$(show_usage)"
        ;;
    *)
        error "Unknown command: $COMMAND" "Run 'kuzu-migrate --help' for usage."
        ;;
esac