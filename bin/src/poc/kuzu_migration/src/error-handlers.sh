#!/usr/bin/env bash
# Error handlers following Don Norman's design principles
# Each error provides clear context, actionable solutions, and prevents mistakes

set -euo pipefail

# Colors for better visibility
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Error handler with Don Norman principles
handle_missing_ddl_directory() {
    local ddl_dir="$1"
    local current_dir=$(pwd)
    
    cat >&2 << EOF
${RED}❌ ERROR: DDL directory not found${NC}

${YELLOW}What happened:${NC}
  I couldn't find the DDL directory at: ${BLUE}${ddl_dir}${NC}
  Current directory: ${BLUE}${current_dir}${NC}

${YELLOW}Why this matters:${NC}
  The DDL directory contains your database migrations and snapshots.
  Without it, I can't manage your database schema changes.

${YELLOW}How to fix this:${NC}
  ${GREEN}Option 1:${NC} Initialize a new DDL directory (recommended)
    $ kuzu-migrate --ddl ${ddl_dir} init

  ${GREEN}Option 2:${NC} Use a different DDL directory
    $ kuzu-migrate --ddl ./path/to/existing/ddl apply

  ${GREEN}Option 3:${NC} Check if you're in the right directory
    $ cd /path/to/your/project
    $ kuzu-migrate apply

${YELLOW}Common causes:${NC}
  • Running the command from the wrong directory
  • Forgot to run 'init' after cloning the project
  • Specified incorrect path with --ddl flag

${BLUE}Learn more:${NC} https://github.com/kuzu-migrate/docs/ddl-structure
EOF
    exit 1
}

handle_migration_syntax_error() {
    local migration_file="$1"
    local error_message="$2"
    local line_number="${3:-}"
    
    cat >&2 << EOF
${RED}❌ ERROR: Invalid Cypher syntax in migration${NC}

${YELLOW}What happened:${NC}
  Migration file has syntax errors: ${BLUE}${migration_file}${NC}
  ${RED}Error: ${error_message}${NC}
  ${line_number:+Line: ${line_number}}

${YELLOW}How to diagnose:${NC}
  ${GREEN}1.${NC} Check the migration file syntax:
    $ cat "${migration_file}"

  ${GREEN}2.${NC} Validate Cypher syntax manually:
    $ kuzu ./test.db
    kuzu> \`cat "${migration_file}"\`

  ${GREEN}3.${NC} Common syntax issues to check:
    • Missing semicolons at end of statements
    • Unclosed parentheses or quotes
    • Invalid property types (use STRING, INT64, DOUBLE, etc.)
    • Typos in keywords (CREATE NODE TABLE, not CREATE TABLE)

${YELLOW}Example of correct syntax:${NC}
  ${BLUE}CREATE NODE TABLE User (
    id INT64 PRIMARY KEY,
    name STRING NOT NULL,
    email STRING UNIQUE
  );${NC}

${YELLOW}How to fix:${NC}
  ${GREEN}Option 1:${NC} Fix the syntax error in the file
    $ \$EDITOR "${migration_file}"

  ${GREEN}Option 2:${NC} Skip this migration (dangerous!)
    $ touch "${migration_file}.skip"
    $ kuzu-migrate apply

${BLUE}Cypher reference:${NC} https://kuzudb.com/docs/cypher/
EOF
    exit 1
}

handle_database_locked() {
    local db_path="$1"
    
    cat >&2 << EOF
${RED}❌ ERROR: Database is locked${NC}

${YELLOW}What happened:${NC}
  Cannot access database at: ${BLUE}${db_path}${NC}
  Another process might be using it.

${YELLOW}How to diagnose:${NC}
  ${GREEN}1.${NC} Check for other KuzuDB processes:
    $ ps aux | grep kuzu

  ${GREEN}2.${NC} Check for lock files:
    $ ls -la "${db_path}"/*.lock

  ${GREEN}3.${NC} Check file permissions:
    $ ls -la "${db_path}"

${YELLOW}How to fix:${NC}
  ${GREEN}Option 1:${NC} Wait and retry (if temporary)
    $ sleep 5 && kuzu-migrate apply

  ${GREEN}Option 2:${NC} Stop other KuzuDB processes
    $ pkill -f kuzu
    $ kuzu-migrate apply

  ${GREEN}Option 3:${NC} Remove stale lock files (use with caution!)
    $ rm -f "${db_path}"/*.lock
    $ kuzu-migrate apply

${YELLOW}Prevention:${NC}
  • Always properly close KuzuDB connections
  • Use connection pooling in applications
  • Implement proper shutdown handlers

${BLUE}Troubleshooting guide:${NC} https://github.com/kuzu-migrate/docs/database-locks
EOF
    exit 1
}

handle_missing_kuzu_cli() {
    local system_type=$(uname -s)
    
    cat >&2 << EOF
${RED}❌ ERROR: KuzuDB CLI not found${NC}

${YELLOW}What happened:${NC}
  The 'kuzu' command is not installed or not in your PATH.

${YELLOW}How to install:${NC}
  ${GREEN}Option 1:${NC} Using Nix (recommended)
    $ nix-env -iA nixpkgs.kuzu
    
  ${GREEN}Option 2:${NC} Using the official installer
    $ curl -fsSL https://kuzudb.com/install.sh | bash
    
  ${GREEN}Option 3:${NC} Platform-specific installation:
EOF
    
    case "$system_type" in
        Darwin)
            echo "    $ brew install kuzu"
            ;;
        Linux)
            echo "    $ wget https://github.com/kuzudb/kuzu/releases/latest/download/kuzu-linux-x64"
            echo "    $ chmod +x kuzu-linux-x64"
            echo "    $ sudo mv kuzu-linux-x64 /usr/local/bin/kuzu"
            ;;
    esac
    
    cat >&2 << EOF

${YELLOW}After installation:${NC}
  1. Verify installation:
     $ kuzu --version
     
  2. Retry your command:
     $ kuzu-migrate apply

${BLUE}Installation guide:${NC} https://kuzudb.com/docs/installation
EOF
    exit 1
}

handle_invalid_migration_name() {
    local file_name="$1"
    local migrations_dir="$2"
    
    cat >&2 << EOF
${RED}❌ ERROR: Invalid migration file name${NC}

${YELLOW}What happened:${NC}
  Migration file doesn't follow naming convention: ${BLUE}${file_name}${NC}

${YELLOW}Expected format:${NC}
  ${GREEN}NNN_description.cypher${NC}
  
  Where:
  • NNN = 3-digit sequence number (000-999)
  • description = snake_case description
  • .cypher = required file extension

${YELLOW}Examples of valid names:${NC}
  ✅ 001_create_user_table.cypher
  ✅ 002_add_email_field.cypher
  ✅ 003_create_indexes.cypher
  
${YELLOW}Examples of invalid names:${NC}
  ❌ 1_create_user.cypher        (need 3 digits: 001)
  ❌ 001-create-user.cypher      (use underscores, not hyphens)
  ❌ 001_CreateUser.cypher       (use snake_case, not CamelCase)
  ❌ 001_create_user.sql         (must be .cypher extension)

${YELLOW}How to fix:${NC}
  ${GREEN}Option 1:${NC} Rename the file
    $ mv "${migrations_dir}/${file_name}" \\
         "${migrations_dir}/$(printf "%03d" \$NEXT_NUMBER)_your_description.cypher"

  ${GREEN}Option 2:${NC} Check existing migrations for the next number
    $ ls -1 "${migrations_dir}" | tail -n 1

${YELLOW}Current migrations:${NC}
$(ls -1 "${migrations_dir}"/*.cypher 2>/dev/null | tail -n 5 || echo "  No migrations found")

${BLUE}Naming guide:${NC} https://github.com/kuzu-migrate/docs/naming-conventions
EOF
    exit 1
}

# Export all handlers
export -f handle_missing_ddl_directory
export -f handle_migration_syntax_error
export -f handle_database_locked
export -f handle_missing_kuzu_cli
export -f handle_invalid_migration_name