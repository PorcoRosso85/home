{ pkgs, kuzu-migrate, ddlPath ? "./ddl" }:
let
  # Single responsibility: validate DDL structure
  validateDDL = pkgs.writeShellApplication {
    name = "validate-ddl";
    runtimeInputs = [ pkgs.coreutils ];
    text = ''
      DDL_DIR="${ddlPath}"
      
      # Source validators
      source ${kuzu-migrate}/share/kuzu-migrate/validators.sh
      
      # Run validations
      if ! validate_ddl_directory "$DDL_DIR"; then
        echo "❌ DDL directory does not exist: $DDL_DIR"
        exit 1
      fi
      
      if ! validate_migrations_directory "$DDL_DIR"; then
        echo "❌ migrations/ subdirectory missing"
        exit 1
      fi
      
      if ! validate_snapshots_directory "$DDL_DIR"; then
        echo "❌ snapshots/ subdirectory missing"
        exit 1
      fi
      
      echo "✅ DDL structure is valid"
    '';
  };
  
  # Single responsibility: validate migration files
  validateMigrations = pkgs.writeShellApplication {
    name = "validate-migrations";
    runtimeInputs = [ pkgs.coreutils ];
    text = ''
      DDL_DIR="${ddlPath}"
      source ${kuzu-migrate}/share/kuzu-migrate/validators.sh
      
      invalid_count=0
      for file in "$DDL_DIR/migrations"/*.cypher; do
        if [[ -f "$file" ]]; then
          basename=$(basename "$file")
          if ! validate_migration_filename "$basename"; then
            echo "❌ Invalid filename: $basename"
            ((invalid_count++))
          fi
          
          if ! validate_cypher_syntax "$file"; then
            echo "❌ Syntax error in: $basename"
            ((invalid_count++))
          fi
        fi
      done
      
      if [[ $invalid_count -eq 0 ]]; then
        echo "✅ All migrations are valid"
      else
        exit 1
      fi
    '';
  };
  
  # Single responsibility: provide error guidance
  provideErrorGuidance = pkgs.writeShellApplication {
    name = "provide-error-guidance";
    runtimeInputs = [ pkgs.coreutils ];
    text = ''
      ERROR_TYPE="''${1:-unknown}"
      ERROR_CONTEXT="''${2:-}"
      
      source ${kuzu-migrate}/share/kuzu-migrate/error-handlers.sh
      
      case "$ERROR_TYPE" in
        missing-ddl)
          handle_missing_ddl_directory "$ERROR_CONTEXT"
          ;;
        invalid-migration-name)
          handle_invalid_migration_name "$ERROR_CONTEXT" "${ddlPath}/migrations"
          ;;
        migration-syntax)
          handle_migration_syntax_error "$ERROR_CONTEXT" "''${3:-}"
          ;;
        database-locked)
          handle_database_locked "$ERROR_CONTEXT"
          ;;
        missing-kuzu)
          handle_missing_kuzu_cli
          ;;
        *)
          echo "Unknown error type: $ERROR_TYPE"
          exit 1
          ;;
      esac
    '';
  };
  
  # Single responsibility: execute migrations (no validation)
  executeMigrations = pkgs.writeShellApplication {
    name = "execute-migrations";
    runtimeInputs = [ kuzu-migrate ];
    text = ''
      exec ${kuzu-migrate}/bin/kuzu-migrate --ddl ${ddlPath} apply --skip-validation
    '';
  };
  
  # Single responsibility: display status (no validation)
  displayStatus = pkgs.writeShellApplication {
    name = "display-status";
    runtimeInputs = [ kuzu-migrate ];
    text = ''
      exec ${kuzu-migrate}/bin/kuzu-migrate --ddl ${ddlPath} status --skip-validation
    '';
  };
in
{
  # Core single-responsibility apps
  validate-structure = {
    type = "app";
    program = "${validateDDL}/bin/validate-ddl";
  };
  
  validate-migrations = {
    type = "app";
    program = "${validateMigrations}/bin/validate-migrations";
  };
  
  show-error-help = {
    type = "app";
    program = "${provideErrorGuidance}/bin/provide-error-guidance";
  };
  
  # Composite apps with Don Norman UX
  migrate = {
    type = "app";
    program = "${pkgs.writeShellScript "migrate-with-guidance" ''
      # Step 1: Validate structure
      if ! ${validateDDL}/bin/validate-ddl 2>/dev/null; then
        ${provideErrorGuidance}/bin/provide-error-guidance missing-ddl "${ddlPath}"
      fi
      
      # Step 2: Validate migrations
      if ! ${validateMigrations}/bin/validate-migrations; then
        echo ""
        echo "❌ Migration validation failed"
        echo "Run 'nix run .#validate-migrations' for details"
        exit 1
      fi
      
      # Step 3: Execute migrations
      ${executeMigrations}/bin/execute-migrations || {
        EXIT_CODE=$?
        echo ""
        echo "❌ Migration execution failed"
        echo "Run 'nix run .#show-error-help migration-syntax <filename>' for guidance"
        exit $EXIT_CODE
      }
    ''}";
  };
  
  init = {
    type = "app";
    program = "${pkgs.writeShellScript "init-with-guidance" ''
      ${kuzu-migrate}/bin/kuzu-migrate --ddl ${ddlPath} init || {
        EXIT_CODE=$?
        if [[ ! -d "${ddlPath}" ]]; then
          echo ""
          echo "📁 Creating parent directory first..."
          mkdir -p "$(dirname "${ddlPath}")"
          ${kuzu-migrate}/bin/kuzu-migrate --ddl ${ddlPath} init
        else
          exit $EXIT_CODE
        fi
      }
    ''}";
  };
  
  status = {
    type = "app";
    program = "${pkgs.writeShellScript "status-with-guidance" ''
      if ! ${validateDDL}/bin/validate-ddl 2>/dev/null; then
        ${provideErrorGuidance}/bin/provide-error-guidance missing-ddl "${ddlPath}"
      fi
      
      ${displayStatus}/bin/display-status
    ''}";
  };
  
  # Diagnostic app for troubleshooting
  diagnose = {
    type = "app";
    program = "${pkgs.writeShellScript "diagnose-issues" ''
      echo "🔍 Diagnosing kuzu-migrate setup..."
      echo ""
      
      echo "1. Checking DDL structure:"
      ${validateDDL}/bin/validate-ddl || echo "   ❌ Structure validation failed"
      echo ""
      
      echo "2. Checking migration files:"
      ${validateMigrations}/bin/validate-migrations || echo "   ❌ Migration validation failed"
      echo ""
      
      echo "3. Checking KuzuDB CLI:"
      if command -v kuzu &>/dev/null; then
        echo "   ✅ KuzuDB CLI found: $(which kuzu)"
        echo "   Version: $(kuzu --version)"
      else
        echo "   ❌ KuzuDB CLI not found"
        echo "   Run: nix run .#show-error-help missing-kuzu"
      fi
      echo ""
      
      echo "4. Current configuration:"
      echo "   DDL Path: ${ddlPath}"
      echo "   DB Path: \$KUZU_DB_PATH (default: ./data/kuzu.db)"
    ''}";
  };
}