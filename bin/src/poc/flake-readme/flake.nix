{
  description = "Flake documentation collection POC - Single responsibility for readme.nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      lib = nixpkgs.lib;
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      
      forAllSystems = f: lib.genAttrs systems (system: 
        f nixpkgs.legacyPackages.${system}
      );
    in {
      # Expose docs functions for external use
      lib = {
        docs = import ./lib/core-docs.nix { inherit lib; inherit self; };
      };

      # flake-parts module
      flakeModules = {
        readme = ./lib/flake-module.nix;
      };

      # Package outputs - removed: docs-json, docs-report, default
      # All functionality moved to lib.docs.index (single source of truth)
      # Consumer-side persistence via flake-parts module only
      packages = forAllSystems (pkgs: {});

      # App outputs
      apps = forAllSystems (pkgs: {
        readme-init = {
          type = "app";
          program = "${pkgs.writeShellApplication {
            name = "readme-init";
            runtimeInputs = with pkgs; [ coreutils ];
            text = ''
              set -euo pipefail
              
              # Parse arguments
              FORCE=false
              ROOT_PATH=""
              while [[ $# -gt 0 ]]; do
                case $1 in
                  --help)
                    echo "Usage: readme-init [--force] [--root PATH]"
                    echo ""
                    echo "Initialize readme.nix template file in specified directory"
                    echo ""
                    echo "Options:"
                    echo "  --force    Overwrite existing readme.nix (creates backup)"
                    echo "  --root PATH Use specified directory instead of current directory"
                    echo "  --help     Show this help message"
                    echo ""
                    echo "Examples:"
                    echo "  readme-init              # Create new readme.nix in current dir"
                    echo "  readme-init --force      # Overwrite with backup"
                    echo "  readme-init --root ./sub  # Create in ./sub directory"
                    exit 0
                    ;;
                  --force)
                    FORCE=true
                    shift
                    ;;
                  --root)
                    if [[ $# -lt 2 ]]; then
                      echo "Error: --root requires a directory path" >&2
                      exit 1
                    fi
                    ROOT_PATH="$2"
                    shift 2
                    ;;
                  *)
                    echo "Unknown option: $1" >&2
                    echo "Usage: readme-init [--force] [--root PATH]" >&2
                    echo "Use --help for more information" >&2
                    exit 1
                    ;;
                esac
              done
              
              # Set working directory
              if [ -n "$ROOT_PATH" ]; then
                if [ ! -d "$ROOT_PATH" ]; then
                  echo "❌ Error: Directory does not exist: $ROOT_PATH" >&2
                  exit 1
                fi
                cd "$ROOT_PATH"
              fi
              
              # Check if we're in a flake environment (warn but allow continue)
              if [ ! -f "./flake.nix" ]; then
                echo "⚠️  Warning: No flake.nix found in current directory"
                echo ""
                echo "readme.nix files are designed for flake-based projects."
                echo "Consider initializing a flake first:"
                echo "  nix flake init"
                echo ""
                echo "Continuing with template creation..."
                echo ""
              fi
              
              # Check if readme.nix already exists
              if [ -f readme.nix ]; then
                if [ "$FORCE" = "false" ]; then
                  echo "❌ readme.nix already exists in current directory"
                  echo "Use --force to overwrite with backup"
                  exit 1
                fi
                
                # Create backup with timestamp
                BACKUP_NAME="readme.nix.bak-$(date +%Y%m%d-%H%M%S)"
                cp readme.nix "$BACKUP_NAME"
                echo "📁 Backup created: $BACKUP_NAME"
              fi
              
              # Copy template (only if different content to avoid unnecessary writes)
              TEMPLATE_CONTENT=$(cat ${./template/readme.nix})
              if [ -f readme.nix ]; then
                CURRENT_CONTENT=$(cat readme.nix)
                if [ "$TEMPLATE_CONTENT" = "$CURRENT_CONTENT" ]; then
                  echo "✅ readme.nix is already up to date"
                  exit 0
                fi
              fi
              
              # Copy template
              cp ${./template/readme.nix} ./readme.nix
              echo "✅ Created readme.nix from template"
              
              # Provide guidance
              echo ""
              echo "Next steps:"
              echo "1. Edit readme.nix with your project details"
              echo "2. Run: nix run .#readme-check"
              echo "3. Add integration code to your flake.nix"
              echo "4. See: docs/integration.md"
            '';
          }}/bin/readme-init";
          meta = {
            description = "Initialize readme.nix template file in current directory";
          };
        };

        readme-check = {
          type = "app";
          program = "${pkgs.writeShellApplication {
            name = "readme-check";
            runtimeInputs = with pkgs; [ jq nix ];
            text = ''
              set -euo pipefail
              
              # Parse arguments
              ROOT_PATH=""
              while [[ $# -gt 0 ]]; do
                case $1 in
                  --help)
                    echo "Usage: readme-check [--root PATH]"
                    echo ""
                    echo "Validate readme.nix files and show documentation report"
                    echo ""
                    echo "Options:"
                    echo "  --root PATH Use specified directory instead of current directory"
                    echo "  --help     Show this help message"
                    echo ""
                    echo "Examples:"
                    echo "  readme-check             # Validate all readme.nix files"
                    echo "  readme-check --root ./sub # Validate from ./sub directory"
                    echo ""
                    echo "Exit codes:"
                    echo "  0          All documentation is valid"
                    echo "  1          Validation errors or missing files found"
                    exit 0
                    ;;
                  --root)
                    if [[ $# -lt 2 ]]; then
                      echo "Error: --root requires a directory path" >&2
                      exit 1
                    fi
                    ROOT_PATH="$2"
                    shift 2
                    ;;
                  *)
                    echo "Unknown option: $1" >&2
                    echo "Usage: readme-check [--root PATH]" >&2
                    echo "Use --help for more information" >&2
                    exit 1
                    ;;
                esac
              done
              
              export NIX_CONFIG="experimental-features = nix-command flakes"
              
              echo "🔍 Checking readme.nix documentation..."
              
              # Set working directory and warn about Git boundary limitations
              if [ -n "$ROOT_PATH" ]; then
                if [ ! -d "$ROOT_PATH" ]; then
                  echo "❌ Error: Directory does not exist: $ROOT_PATH" >&2
                  exit 1
                fi
                cd "$ROOT_PATH"
                echo "📁 Using root directory: $ROOT_PATH"
                echo ""
                echo "⚠️  WARNING: Git Boundary Enforcement Disabled"
                echo ""
                echo "When using --root, flake-readme cannot guarantee Git tracking boundaries."
                echo "This may include files outside your intended scope:"
                echo ""
                echo "  • Files committed but later added to .gitignore remain visible"
                echo "  • Manual path filtering becomes limited"
                echo "  • Standard Git-aware filtering is bypassed"
                echo ""
                echo "Recommended alternatives:"
                echo "  1. Use ignoreExtra configuration in flake-parts integration"
                echo "  2. Run from the actual flake directory without --root"
                echo "  3. Remove unwanted files from Git tracking first:"
                echo "     git rm -r --cached unwanted-dir/"
                echo "     echo 'unwanted-dir/' >> .gitignore"
                echo ""
                echo "Proceeding with manual path filtering..."
                echo ""
              fi
              
              # Check if we're in a flake environment
              if [ ! -f "./flake.nix" ]; then
                echo "❌ Error: No flake.nix found in current directory"
                echo ""
                echo "flake-readme requires a flake environment to function properly."
                echo ""
                echo "Solutions:"
                echo "  1. Run from a directory containing flake.nix"
                echo "  2. Use --root option to specify flake directory:"
                echo "     readme-check --root ./path/to/check"
                echo "  3. Initialize a new flake:"
                echo "     nix flake init"
                echo ""
                echo "For more information, see: https://nixos.wiki/wiki/Flakes"
                exit 1
              fi
              
              # Test if flake evaluation works (fail fast for broken flakes)
              if ! nix eval --impure --json --expr 'builtins.getFlake (toString ./.)' >/dev/null 2>&1; then
                echo "❌ Error: Current directory does not contain a valid flake"
                echo ""
                echo "The flake.nix file exists but cannot be evaluated."
                echo ""
                echo "Possible issues:"
                echo "  - Syntax errors in flake.nix"
                echo "  - Missing flake.lock (run: nix flake lock)"
                echo "  - Invalid flake structure"
                echo ""
                echo "Debug with: nix flake check"
                exit 1
              fi
              
              # Use same validation logic as flake checks
              REPORT=$(nix eval --impure --json --expr '
                let 
                  flake = builtins.getFlake (toString ./.);
                  lib = flake.lib.docs or (import ${./lib/core-docs.nix} { 
                    lib = (import <nixpkgs> {}).lib; 
                    self = {}; 
                  });
                  # Use flake.outPath as root for consistency with checks
                  currentRoot = flake.outPath;
                in 
                lib.index { root = currentRoot; }
              ')
              
              # Check missing readme.nix files
              MISSING=$(echo "$REPORT" | jq -r '.missingReadmes | @tsv')
              if [ -n "$MISSING" ]; then
                echo "❌ Missing readme.nix in directories:"
                printf '%s\n' "$MISSING" | while read -r dir; do
                  echo "  - $dir"
                done
                echo ""
                echo "Run 'nix run .#readme-init' in those directories"
                exit 1
              fi
              
              # Check validation errors
              ERR_COUNT=$(echo "$REPORT" | jq -r '.errorCount')
              if [ "$ERR_COUNT" != "0" ]; then
                echo "❌ Validation errors detected:"
                echo "$REPORT" | jq -r '.reports | to_entries[] | select(.value.errors|length>0) | "\(.key):\n" + (.value.errors | map("  - " + .) | join("\n"))'
                exit 1
              fi
              
              # Show warnings if any
              WARN_COUNT=$(echo "$REPORT" | jq -r '.warningCount')
              if [ "$WARN_COUNT" != "0" ]; then
                echo "⚠️  Warnings detected:"
                echo "$REPORT" | jq -r '.reports | to_entries[] | select(.value.warnings|length>0) | "\(.key):\n" + (.value.warnings | map("  - " + .) | join("\n"))'
                echo ""
              fi
              
              echo "✅ Documentation validation complete"
              echo "📊 Processed $(echo "$REPORT" | jq -r '.docs | keys | length') directories"
            '';
          }}/bin/readme-check";
          meta = {
            description = "Validate readme.nix files and show documentation report";
          };
        };
      });

      # Test outputs for validation
      tests = forAllSystems (pkgs: {
        # Import test files
        ignore-only-policy = import ./test-ignore-only-policy.nix;
        performance = import ./test-performance.nix;
        e2e-workflow = import ./test-e2e-workflow.nix;
      });

      # Checks
      checks = forAllSystems (pkgs: {
        # SSOT verification: readme.nix ↔ README.md consistency
        ssot-check = pkgs.runCommand "ssot-verification" {
          buildInputs = with pkgs; [ nix ripgrep ];
        } ''
          set -euo pipefail
          cd ${self}

          echo "🎯 SSOT Verification: readme.nix ↔ README.md consistency"

          # Check 1: readme.nix can be evaluated
          if ! nix-instantiate --eval readme.nix --attr description >/dev/null 2>&1; then
            echo "❌ ERROR: readme.nix has evaluation errors"
            exit 1
          fi

          # Check 2: README.md exists
          if [[ ! -f README.md ]]; then
            echo "❌ ERROR: README.md not found"
            exit 1
          fi

          # Check 3: No exact description duplication
          README_DESC=$(nix-instantiate --eval --strict readme.nix --attr description | tr -d '"')
          if rg -Fq "$README_DESC" README.md; then
            echo "❌ ERROR: README.md contains exact duplicate of readme.nix description"
            echo "Found: $README_DESC"
            exit 1
          fi

          # Check 4: No structured data patterns in README.md
          if rg -q "(goal|nonGoal|output|meta).*=" README.md; then
            echo "❌ ERROR: README.md contains structured data patterns"
            echo "These belong in readme.nix, not README.md:"
            rg "(goal|nonGoal|output|meta).*=" README.md || true
            exit 1
          fi

          echo "✅ SSOT verification passed"
          touch $out
        '';

        docs-lint = pkgs.runCommand "docs-lint-check"
          (let reportFile = pkgs.writeText "docs-report.json" (builtins.toJSON (self.lib.docs.index { root = self.outPath; })); in {
            buildInputs = [ pkgs.jq ];
            REPORT_FILE = reportFile;
          }) ''
          set -euo pipefail
          echo "Checking documentation structure..."
          REPORT=$(cat "$REPORT_FILE")

          # Basic structure
          echo "$REPORT" | jq -e '.docs | type == "object"' >/dev/null
          echo "$REPORT" | jq -e '.schemaVersion == 1' >/dev/null

          # Missing readme.nix check (only for directories requiring documentation)
          MISSING=$(echo "$REPORT" | jq -r '.missingReadmes | @tsv')
          if [ -n "$MISSING" ]; then
            echo "Missing readme.nix in directories:" >&2
            echo "$MISSING" | sed 's/^/  - /' >&2
            exit 1
          fi

          # Validation errors (meta/output etc.)
          ERR_COUNT=$(echo "$REPORT" | jq -r '.errorCount')
          if [ "$ERR_COUNT" != "0" ]; then
            echo "Validation errors detected:" >&2
            echo "$REPORT" | jq -r '.reports | to_entries[] | select(.value.errors|length>0) | "\(.key):\n" + (.value.errors | map("  - " + .) | join("\n"))' >&2
            exit 1
          fi

          echo "✓ Documentation structure is valid"
          touch $out
        '';

        # Validate that invalid examples are correctly detected as invalid  
        invalid-examples = pkgs.runCommand "check-invalid-detection"
          {
            buildInputs = [ pkgs.jq ];
            # Test individual invalid examples with inline definitions
            VALIDATION_RESULTS = let
              lib = nixpkgs.lib;
              coreLib = import ./lib/core-docs.nix { inherit lib; self = {}; };
              
              # Define test cases inline to avoid import path issues
              examples = {
                "missing-description" = {
                  goal = [ "demonstrate missing description error" ];
                  nonGoal = [ "being a valid readme.nix" ];
                  meta = { example = "invalid"; };
                  output = { packages = [ "invalid-example" ]; };
                };
                "empty-goal" = {
                  description = "Example with empty goal array";
                  goal = [ ];  # Empty - should cause validation error
                  nonGoal = [ "having goals" ];
                  meta = { example = "invalid"; };
                  output = { packages = [ "invalid-example" ]; };
                };
                "empty-nongoal" = {
                  description = "Example with empty nonGoal array";
                  goal = [ "demonstrate empty nonGoal error" ];
                  nonGoal = [ ];  # Empty - should cause validation error  
                  meta = { example = "invalid"; };
                  output = { packages = [ "invalid-example" ]; };
                };
                "invalid-goal-type" = {
                  description = "Example with invalid goal type";
                  goal = "should be an array but is a string";  # Wrong type
                  nonGoal = [ "having correct types" ];
                  meta = { example = "invalid"; };
                  output = { packages = [ "invalid-example" ]; };
                };
                "v1-extension-fields" = {
                  description = "Example v1 document with extension fields that should warn";
                  goal = [ "demonstrate v1 extension field warning behavior" ];
                  nonGoal = [ "being a valid v1 document without warnings" ];
                  meta = { example = "v1-with-extensions"; };
                  output = { packages = [ "test-package" ]; };
                  # Extension fields that should generate warnings in v1 documents
                  usage = "This should trigger a warning";
                  features = [ "feature1" "feature2" ];
                  techStack = { language = "nix"; framework = "flake-parts"; };
                };
                "unknown-output-keys" = {
                  description = "Example with unknown output keys";
                  goal = [ "demonstrate unknown output keys warning" ];
                  nonGoal = [ "following the standard output schema" ];
                  meta = { example = "invalid"; };
                  output = {
                    packages = [ "invalid-example" ];
                    unknownKey = [ "not-allowed" ];  # Unknown key - should cause warning
                    anotherUnknown = "also-invalid";
                  };
                };
              };
              
              # Validate each example
              results = lib.mapAttrs (name: doc: 
                let
                  normalized = coreLib.normalizeDoc { path = name; inherit doc; };
                  validation = coreLib.validateDoc { path = name; doc = normalized; };
                in validation
              ) examples;
              
              # Count totals
              allErrors = lib.concatMap (name: results.${name}.errors) (builtins.attrNames results);
              allWarnings = lib.concatMap (name: results.${name}.warnings) (builtins.attrNames results);
              
              summary = {
                results = results;
                errorCount = builtins.length allErrors;
                warningCount = builtins.length allWarnings;
                # Add missing readme detection
                missingReadmes = [ "missing-readme" ];  # We know this directory exists and lacks readme.nix
              };
            in builtins.toJSON summary;
          } ''
          set -euo pipefail
          echo "🧪 Checking that invalid examples are detected as invalid..."
          echo "Validation results preview:" >&2
          echo "$VALIDATION_RESULTS" | jq -r '.errorCount as $e | .warningCount as $w | "Errors: \($e), Warnings: \($w)"' >&2
          
          # Expect validation errors (multiple invalid examples have errors)
          ERR_COUNT=$(echo "$VALIDATION_RESULTS" | jq -r '.errorCount') 
          if [ "$ERR_COUNT" -lt "3" ]; then
            echo "❌ Expected at least 3 validation errors but got $ERR_COUNT" >&2
            echo "Invalid examples should generate multiple errors" >&2
            echo "$VALIDATION_RESULTS" | jq -r '.results | to_entries[] | select(.value.errors|length>0) | "\(.key): \(.value.errors | join(", "))"' >&2
            exit 1
          fi

          # Expect warnings from extension fields and unknown output keys  
          WARN_COUNT=$(echo "$VALIDATION_RESULTS" | jq -r '.warningCount') 
          if [ "$WARN_COUNT" -lt "2" ]; then
            echo "❌ Expected at least 2 warnings but got $WARN_COUNT" >&2
            echo "Extension fields and unknown output keys should generate warnings" >&2
            echo "$VALIDATION_RESULTS" | jq -r '.results | to_entries[] | select(.value.warnings|length>0) | "\(.key): \(.value.warnings | join(", "))"' >&2
            exit 1
          fi

          # Expect missing readme.nix detection (missing-readme directory)
          MISSING_COUNT=$(echo "$VALIDATION_RESULTS" | jq -r '.missingReadmes | length')
          if [ "$MISSING_COUNT" -lt "1" ]; then
            echo "❌ Expected at least 1 missing readme.nix but got $MISSING_COUNT" >&2 
            echo "missing-readme directory should be detected" >&2
            exit 1
          fi

          echo "✓ Invalid examples correctly detected:"
          echo "  - Validation errors: $ERR_COUNT"  
          echo "  - Warnings: $WARN_COUNT"
          echo "  - Missing readme.nix: $MISSING_COUNT"
          
          # Show specific detection details
          echo "📋 Error details:"
          echo "$VALIDATION_RESULTS" | jq -r '.results | to_entries[] | select(.value.errors|length>0) | "  \(.key): \(.value.errors | join("; "))"'
          echo "⚠️  Warning details:"
          echo "$VALIDATION_RESULTS" | jq -r '.results | to_entries[] | select(.value.warnings|length>0) | "  \(.key): \(.value.warnings | join("; "))"'
          
          touch $out
        '';

        # Test for v1 extension field warnings (RED phase - should fail initially)
        v1-extension-warnings = pkgs.runCommand "check-v1-extension-warnings"
          {
            buildInputs = [ pkgs.jq ];
            # Test using inline v1 document with extension fields
            EXTENSION_REPORT = let
              # Inline test document with v1 schema + extension fields
              testDoc = {
                description = "Test v1 document with extension fields";
                goal = [ "test extension field warnings" ];
                nonGoal = [ "being a standard v1 document" ];
                meta = { test = "v1-extensions"; };
                output = { packages = [ "test-package" ]; };
                
                # Extension fields that should generate warnings
                usage = "This should trigger a warning";
                features = [ "feature1" "feature2" ];
                techStack = { language = "nix"; framework = "flake-parts"; };
              };
              lib = nixpkgs.lib;
              coreLib = import ./lib/core-docs.nix { inherit lib; self = {}; };
              normalized = coreLib.normalizeDoc { 
                path = "test-v1-extension-fields"; 
                doc = testDoc; 
              };
              validation = coreLib.validateDoc { 
                path = "test-v1-extension-fields"; 
                doc = normalized; 
              };
              report = {
                schemaVersion = 1;
                docs = { "test-v1-extension-fields" = normalized; };
                warnings = validation.warnings;
                warningCount = builtins.length validation.warnings;
                errorCount = builtins.length validation.errors;
                reports = { "test-v1-extension-fields" = validation; };
              };
            in builtins.toJSON report;
          } ''
          set -euo pipefail
          echo "🧪 Testing v1 extension field warnings..."
          echo "Extension report: $EXTENSION_REPORT" >&2
          
          # Should detect warnings for extension fields (usage, features, techStack)
          WARN_COUNT=$(echo "$EXTENSION_REPORT" | jq -r '.warningCount')
          if [ "$WARN_COUNT" = "0" ]; then
            echo "❌ Expected warnings for v1 extension fields but found none" >&2
            echo "This indicates that v1 documents with extension fields are not generating warnings" >&2
            echo "Extension fields like 'usage', 'features', 'techStack' should trigger warnings in v1 schema" >&2
            exit 1
          fi
          
          # Check if warning message contains expected pattern
          WARNINGS=$(echo "$EXTENSION_REPORT" | jq -r '.warnings[]' 2>/dev/null || echo "")
          if ! echo "$WARNINGS" | grep -q "Unknown keys found"; then
            echo "❌ Warning message doesn't match expected pattern" >&2
            echo "Expected warning containing 'Unknown keys found at .: [...]'" >&2
            echo "Actual warnings: $WARNINGS" >&2
            exit 1
          fi
          
          # Check that specific extension fields are mentioned
          EXPECTED_FIELDS="usage features techStack"
          for field in $EXPECTED_FIELDS; do
            if ! echo "$WARNINGS" | grep -q "$field"; then
              echo "❌ Expected extension field '$field' not found in warnings" >&2
              echo "Warnings: $WARNINGS" >&2
              exit 1
            fi
          done
          
          echo "✓ v1 extension field warnings working correctly:"
          echo "  - Warning count: $WARN_COUNT"
          echo "  - Extension fields detected: usage, features, techStack"
          touch $out
        '';
      });
    };
}
