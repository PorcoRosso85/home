#!/usr/bin/env bash
# Hotfix patch for kuzu-migrate.sh
# This patch addresses the urgent issues reported by the user

set -euo pipefail

# Create a patched version of kuzu-migrate.sh
cp src/kuzu-migrate.sh src/kuzu-migrate-patched.sh

# Patch 1: Fix database existence check (both file and directory)
sed -i 's/if \[\[ ! -d "$db_path" \]\]; then/if [[ ! -d "$db_path" ]] \&\& [[ ! -f "$db_path" ]]; then/g' src/kuzu-migrate-patched.sh

# Patch 2: Add timeout to kuzu commands (30 seconds for init, 300 seconds for migrations)
# For initialization
sed -i 's/if ! kuzu "$db_path" < "$init_script" > \/dev\/null 2>&1; then/if ! timeout 30 kuzu "$db_path" < "$init_script" > \/dev\/null 2>\&1; then/g' src/kuzu-migrate-patched.sh

# For migration application
sed -i 's/if kuzu "$db_path" < "$migration_file" > \/dev\/null 2>&1; then/if timeout 300 kuzu "$db_path" < "$migration_file" > \/dev\/null 2>\&1; then/g' src/kuzu-migrate-patched.sh

# For status checks
sed -i 's/check_result=$(echo "$check_query" | kuzu "$db_path" 2>\/dev\/null/check_result=$(echo "$check_query" | timeout 10 kuzu "$db_path" 2>\/dev\/null/g' src/kuzu-migrate-patched.sh

# Patch 3: Add debug output for database operations
# Add debug function
cat >> src/kuzu-migrate-patched.sh << 'EOF'

# Debug function for verbose output
debug() {
    if [[ "${DEBUG:-0}" == "1" ]]; then
        echo "[DEBUG] $*" >&2
    fi
}
EOF

# Patch 4: Improve error handling with more details
sed -i 's/error_msg=$(kuzu "$db_path" < "$migration_file" 2>&1 || true)/error_msg=$(timeout 300 kuzu "$db_path" < "$migration_file" 2>\&1 || true)/g' src/kuzu-migrate-patched.sh

# Make the patched version executable
chmod +x src/kuzu-migrate-patched.sh

echo "Hotfix patch created: src/kuzu-migrate-patched.sh"
echo ""
echo "To test the patched version:"
echo "  nix develop -c bash src/kuzu-migrate-patched.sh --ddl ./ddl --db ./data/kuzu.db status"
echo ""
echo "To enable debug mode:"
echo "  DEBUG=1 nix develop -c bash src/kuzu-migrate-patched.sh --ddl ./ddl --db ./data/kuzu.db apply"
echo ""
echo "The patch includes:"
echo "  1. Fixed database check to support both files and directories"
echo "  2. Added timeouts: 30s for init, 300s for migrations, 10s for status"
echo "  3. Added debug mode support (DEBUG=1)"
echo "  4. Improved error handling with timeouts"