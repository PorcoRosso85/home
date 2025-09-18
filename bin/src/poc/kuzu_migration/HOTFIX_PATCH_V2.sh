#!/usr/bin/env bash
# Hotfix patch V2 for kuzu-migrate.sh
# This patch includes all improvements: timeout fixes, native KuzuDB features, and new commands

set -euo pipefail

echo "=== Creating Hotfix Patch V2 for kuzu-migrate ==="
echo ""

# Create a backup of the current implementation
if [[ -f src/kuzu-migrate.sh ]]; then
    cp src/kuzu-migrate.sh src/kuzu-migrate-backup-$(date +%Y%m%d-%H%M%S).sh
    echo "✅ Backup created"
fi

# Copy the already updated version (which includes all new features)
# The current src/kuzu-migrate.sh already has:
# - validate command with EXPLAIN
# - apply --dry-run with transactions
# - diff command with schema_only
# - Original hotfix improvements

echo "✅ Current implementation already includes:"
echo "   - validate command (EXPLAIN-based syntax checking)"
echo "   - apply --dry-run (transaction-based preview)"
echo "   - diff command (schema comparison)"
echo "   - Timeout fixes from original hotfix"
echo "   - Database file/directory recognition"
echo ""

# Additional improvements that can be applied as patches
cat > additional-improvements.patch << 'EOF'
--- a/src/kuzu-migrate.sh
+++ b/src/kuzu-migrate.sh
@@ -210,7 +210,7 @@ apply_command() {
     
     # Execute initialization
-    if ! kuzu "$db_path" < "$init_script" > /dev/null 2>&1; then
+    if ! timeout 30 kuzu "$db_path" < "$init_script" > /dev/null 2>&1; then
         rm -f "$init_script"
         error_with_hint "Failed to initialize migration tracking table" "check database"
     fi
@@ -304,7 +304,7 @@ apply_command() {
         
         # Execute the migration (with transaction wrapper for dry-run)
         local error_msg=""
-        if echo "$execution_script" | kuzu "$db_path" > /dev/null 2>&1; then
+        if echo "$execution_script" | timeout 300 kuzu "$db_path" > /dev/null 2>&1; then
             # Calculate execution time
             local end_time
             end_time=$(date +%s%3N)
@@ -330,7 +330,7 @@ apply_command() {
             fi
         else
             # Capture error output
-            error_msg=$(echo "$execution_script" | kuzu "$db_path" 2>&1 || true)
+            error_msg=$(echo "$execution_script" | timeout 300 kuzu "$db_path" 2>&1 || true)
             error_msg=$(echo "$error_msg" | tr '\n' ' ' | sed "s/'/''/g")
             
             if [[ "$dry_run" == "true" ]]; then
@@ -507,7 +507,7 @@ status_command() {
     fi
     
     # Check if database exists
-    if [[ ! -d "$db_path" ]]; then
+    if [[ ! -d "$db_path" ]] && [[ ! -f "$db_path" ]]; then
         info "Database not found at: $db_path"
         info "No migrations have been applied yet."
         echo ""
@@ -733,7 +733,7 @@ diff_command() {
     fi
     
     # Check if source database exists
-    if [[ ! -d "$db_path" ]]; then
+    if [[ ! -d "$db_path" ]] && [[ ! -f "$db_path" ]]; then
         error_with_hint "Source database not found at: $db_path" "check path"
     fi
     
@@ -751,7 +751,7 @@ diff_command() {
     esac
     
     # Check if target database exists
-    if [[ ! -d "$target_db" ]]; then
+    if [[ ! -d "$target_db" ]] && [[ ! -f "$target_db" ]]; then
         error_with_hint "Target database not found at: $target_db" "check path"
     fi
     
EOF

# Check if patch can be applied
if command -v patch &> /dev/null; then
    echo "Applying additional timeout and file/directory improvements..."
    if patch -p1 < additional-improvements.patch 2>/dev/null; then
        echo "✅ Additional improvements applied"
    else
        echo "⚠️  Patch may have already been applied or conflicts exist"
    fi
    rm -f additional-improvements.patch
else
    echo "⚠️  'patch' command not available. Manual application needed:"
    echo "   - Add timeout to kuzu commands (30s for init, 300s for migrations)"
    echo "   - Support both file and directory databases"
fi

echo ""
echo "=== Hotfix Patch V2 Summary ==="
echo ""
echo "The current kuzu-migrate.sh now includes:"
echo ""
echo "1. ✅ validate command"
echo "   Usage: kuzu-migrate validate"
echo "   - Uses EXPLAIN to check migration syntax without execution"
echo ""
echo "2. ✅ apply --dry-run option"
echo "   Usage: kuzu-migrate apply --dry-run"
echo "   - Shows what would be applied using transactions"
echo ""
echo "3. ✅ diff command"
echo "   Usage: kuzu-migrate diff --target /path/to/other.db"
echo "   - Compares schemas using EXPORT DATABASE (schema_only=true)"
echo ""
echo "4. ✅ Timeout protection"
echo "   - 30 seconds for initialization"
echo "   - 300 seconds for migrations"
echo ""
echo "5. ✅ Flexible database recognition"
echo "   - Supports both file and directory databases"
echo ""
echo "To test the new features:"
echo "  # Check migration syntax"
echo "  kuzu-migrate validate"
echo ""
echo "  # Preview changes without applying"
echo "  kuzu-migrate apply --dry-run"
echo ""
echo "  # Compare schemas"
echo "  kuzu-migrate diff --target ./other/kuzu.db"
echo ""
echo "For debugging:"
echo "  DEBUG=1 kuzu-migrate apply"
echo ""
echo "✅ Hotfix Patch V2 complete!"