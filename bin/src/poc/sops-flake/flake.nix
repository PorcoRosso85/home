{
  description = "Sops-enabled application with pure Nix implementation";

  inputs = {
    # Pin specific nixpkgs version for reproducibility
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.11";
    
    # Pin specific sops-nix version
    sops-nix = {
      url = "github:Mic92/sops-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    
    flake-utils.url = "github:numtide/flake-utils/v1.0.0";
  };

  outputs = { self, nixpkgs, sops-nix, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        # Pure package definition
        packages.default = pkgs.writeShellScriptBin "sops-app" ''
          echo "Sops-app running with deterministic dependencies"
        '';
        
        # Pure encryption function (no side effects)
        packages.encrypt-pure = pkgs.writeShellApplication {
          name = "encrypt-pure";
          runtimeInputs = [ pkgs.sops ];
          text = ''
            set -euo pipefail
            
            INPUT="''${1:?Input file required}"
            OUTPUT="''${2:-$INPUT.encrypted}"
            
            if [[ ! -f "$INPUT" ]]; then
              echo "Error: Input file $INPUT not found"
              exit 1
            fi
            
            # Create new file, never modify original
            sops -e "$INPUT" > "$OUTPUT"
            echo "✅ Created encrypted file: $OUTPUT"
            echo "ℹ️  Original file unchanged: $INPUT"
          '';
        };
        
        # Development shell with Secret-First tools
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            sops
            age
            ssh-to-age
            gnupg
            jq
            yq
            pre-commit  # Added for Secret-First framework
          ];

          shellHook = ''
            echo "🔐 Secret-First SOPS development environment"
            echo "============================================="
            echo "Available commands:"
            echo "  nix run .#secrets-init     - Initialize secrets setup"
            echo "  nix run .#secrets-edit     - Edit encrypted secrets"
            echo "  pre-commit install        - Enable git hooks"
            echo "  ./scripts/check-no-plaintext-secrets.sh - Manual check"
            echo ""

            # Pre-commit setup guidance
            if [[ ! -f .git/hooks/pre-commit ]]; then
              echo "🚀 To enable Secret-First protection:"
              echo "   pre-commit install"
              echo ""
            fi

            # Age key detection
            if [[ -f ~/.config/sops/age/keys.txt ]]; then
              export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt
              echo "✓ Age key configured: $SOPS_AGE_KEY_FILE"
            fi
            
            # SSH key detection (新規追加)
            if [[ -f ~/.ssh/id_ed25519 ]] || [[ -f ~/.ssh/id_rsa ]]; then
              echo "✓ SSH keys available for age conversion"
              echo "  Convert to age: ssh-to-age -i ~/.ssh/id_ed25519.pub"
            fi
          '';
        };

        # Secret-First checks for CI/CD
        checks = {
          secrets = pkgs.runCommand "secrets-guard" {
            buildInputs = [ pkgs.bash pkgs.gnugrep pkgs.findutils ];
          } ''
            # Copy scripts to build environment
            mkdir -p scripts
            cp ${./scripts/check-no-plaintext-secrets.sh} scripts/check-no-plaintext-secrets.sh
            chmod +x scripts/check-no-plaintext-secrets.sh

            # Run the check (will succeed if no secrets dir or all encrypted)
            bash scripts/check-no-plaintext-secrets.sh

            # Create success marker
            touch $out
          '';
        };

        # Secret-First management applications
        apps = {
          secrets-init = {
            type = "app";
            program = "${pkgs.writeShellScript "secrets-init" ''
              set -euo pipefail

              # Parse command line arguments
              FORCE_MODE=false
              DRY_RUN=false
              SECRET_FILE="app.yaml"

              usage() {
                cat << EOF
Usage: nix run .#secrets-init [OPTIONS]

Secret-First SOPS initialization with idempotent operation modes.

OPTIONS:
    -f, --force         Recreate existing files (non-idempotent mode)
    -n, --dry-run      Show what would be done without making changes
    -s, --secret FILE  Initial secret file name (default: app.yaml)
    -h, --help         Show this help message

EXAMPLES:
    nix run .#secrets-init                    # Standard idempotent setup
    nix run .#secrets-init --force            # Force recreate all files
    nix run .#secrets-init --dry-run          # Preview changes
    nix run .#secrets-init -s database.yaml  # Create database.yaml instead
EOF
              }

              while [[ $# -gt 0 ]]; do
                case $1 in
                  -f|--force) FORCE_MODE=true; shift ;;
                  -n|--dry-run) DRY_RUN=true; shift ;;
                  -s|--secret) SECRET_FILE="$2"; shift 2 ;;
                  -h|--help) usage; exit 0 ;;
                  *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
                esac
              done

              echo "🔧 Secret-First initialization ($([ "$DRY_RUN" = true ] && echo "DRY RUN" || echo "$([ "$FORCE_MODE" = true ] && echo "FORCE MODE" || echo "IDEMPOTENT MODE")"))"
              echo "==============================="

              # Status tracking
              CHANGES_MADE=0
              ALREADY_EXISTS=0

              # Check for age key
              KEY_FILE="$HOME/.config/sops/age/keys.txt"
              if [[ ! -f "$KEY_FILE" ]]; then
                echo "❌ No age key found. Generate one with:"
                echo "   mkdir -p ~/.config/sops/age"
                echo "   age-keygen -o ~/.config/sops/age/keys.txt"
                echo ""
                exit 1
              fi

              echo "✓ Age key found: $KEY_FILE"
              PUBLIC_KEY=$(${pkgs.age}/bin/age-keygen -y "$KEY_FILE")
              echo "✓ Public key: $PUBLIC_KEY"

              # Handle .sops.yaml
              if [[ -f .sops.yaml ]] && [[ "$FORCE_MODE" = false ]]; then
                echo "ℹ️  .sops.yaml already exists (use --force to recreate)"
                ((ALREADY_EXISTS++))

                # Validate existing configuration
                if grep -q "$PUBLIC_KEY" .sops.yaml; then
                  echo "✓ Current public key found in .sops.yaml"
                else
                  echo "⚠️  Current public key NOT found in .sops.yaml"
                  echo "   Consider using --force to update configuration"
                fi
              else
                ACTION="$([ -f .sops.yaml ] && echo "Recreating" || echo "Creating")"
                echo "$ACTION .sops.yaml..."

                if [[ "$DRY_RUN" = false ]]; then
                  cat > .sops.yaml <<EOF
# Secret-First SOPS configuration
# Generated: $(date -Iseconds)
creation_rules:
  - path_regex: secrets/.*\\.(yaml|yml|json)$
    key_groups:
      - age:
          - $PUBLIC_KEY
EOF
                  echo "✓ $ACTION .sops.yaml"
                  ((CHANGES_MADE++))
                else
                  echo "🔍 Would $ACTION .sops.yaml with current public key"
                fi
              fi

              # Handle secrets directory
              if [[ -d secrets ]]; then
                echo "ℹ️  secrets/ directory already exists"
                ((ALREADY_EXISTS++))
              else
                echo "Creating secrets/ directory..."
                if [[ "$DRY_RUN" = false ]]; then
                  mkdir -p secrets
                  echo "✓ Created secrets/ directory"
                  ((CHANGES_MADE++))
                else
                  echo "🔍 Would create secrets/ directory"
                fi
              fi

              # Handle initial secret file
              SECRET_PATH="secrets/$SECRET_FILE"
              if [[ -f "$SECRET_PATH" ]] && [[ "$FORCE_MODE" = false ]]; then
                echo "ℹ️  $SECRET_PATH already exists (use --force to recreate)"
                ((ALREADY_EXISTS++))
              else
                ACTION="$([ -f "$SECRET_PATH" ] && echo "Recreating" || echo "Creating")"
                echo "$ACTION initial secrets file: $SECRET_PATH..."

                if [[ "$DRY_RUN" = false ]]; then
                  cat > /tmp/secret_template.yaml <<EOF
# Initial secrets file - edit with: nix run .#secrets-edit
# Generated: $(date -Iseconds)
api_key: your_api_key_here
database_url: your_database_url_here
EOF
                  ${pkgs.sops}/bin/sops -e /tmp/secret_template.yaml > "$SECRET_PATH"
                  rm /tmp/secret_template.yaml
                  echo "✓ $ACTION encrypted $SECRET_PATH"
                  ((CHANGES_MADE++))
                else
                  echo "🔍 Would $ACTION encrypted $SECRET_PATH"
                fi
              fi

              echo ""
              echo "📊 Summary:"
              echo "  Changes made: $CHANGES_MADE"
              echo "  Already exists: $ALREADY_EXISTS"

              if [[ "$DRY_RUN" = false ]]; then
                if [[ $CHANGES_MADE -gt 0 ]]; then
                  echo ""
                  echo "🚀 Secret-First setup complete!"
                  echo "Next steps:"
                  echo "  1. nix run .#secrets-edit -- $SECRET_FILE  # Edit your secrets"
                  echo "  2. pre-commit install                      # Enable git hooks"
                else
                  echo ""
                  echo "✅ Secret-First already configured (idempotent)"
                  echo "Available commands:"
                  echo "  - nix run .#secrets-edit -- $SECRET_FILE   # Edit secrets"
                  echo "  - nix run .#secrets-init -- --force        # Force recreate"
                fi
              else
                echo ""
                echo "🔍 Dry run complete - no changes made"
                echo "Run without --dry-run to apply changes"
              fi
            ''}";
          };

          secrets-edit = {
            type = "app";
            program = "${pkgs.writeShellScript "secrets-edit" ''
              set -euo pipefail

              # Parse arguments
              SECRET_FILE="app.yaml"
              CREATE_MODE=false

              usage() {
                cat << EOF
Usage: nix run .#secrets-edit [OPTIONS] [SECRET_FILE]

Edit encrypted secrets with SOPS in Secret-First mode.

ARGUMENTS:
    SECRET_FILE         Secret file to edit (default: app.yaml)

OPTIONS:
    -c, --create       Create file if it doesn't exist
    -h, --help         Show this help message

EXAMPLES:
    nix run .#secrets-edit                      # Edit secrets/app.yaml
    nix run .#secrets-edit database.yaml        # Edit secrets/database.yaml
    nix run .#secrets-edit -c new-service.yaml  # Create and edit new file
EOF
              }

              # Handle options and positional arguments
              while [[ $# -gt 0 ]]; do
                case $1 in
                  -c|--create) CREATE_MODE=true; shift ;;
                  -h|--help) usage; exit 0 ;;
                  -*) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
                  *) SECRET_FILE="$1"; shift ;;
                esac
              done

              # Ensure .yaml extension
              if [[ "$SECRET_FILE" != *.yaml ]] && [[ "$SECRET_FILE" != *.yml ]] && [[ "$SECRET_FILE" != *.json ]]; then
                SECRET_FILE="$SECRET_FILE.yaml"
              fi

              SECRET_PATH="secrets/$SECRET_FILE"

              echo "🔐 Secret-First editor"
              echo "====================="
              echo "Target: $SECRET_PATH"

              # Check prerequisites
              if [[ ! -f .sops.yaml ]]; then
                echo "❌ No .sops.yaml configuration found"
                echo "   Run: nix run .#secrets-init"
                exit 1
              fi

              if [[ ! -d secrets ]]; then
                echo "❌ No secrets/ directory found"
                echo "   Run: nix run .#secrets-init"
                exit 1
              fi

              # Handle file creation
              if [[ ! -f "$SECRET_PATH" ]]; then
                if [[ "$CREATE_MODE" = true ]]; then
                  echo "Creating new encrypted file: $SECRET_PATH"
                  cat > /tmp/new_secret.yaml <<EOF
# New secrets file: $SECRET_FILE
# Add your secrets below
example_key: example_value
EOF
                  ${pkgs.sops}/bin/sops -e /tmp/new_secret.yaml > "$SECRET_PATH"
                  rm /tmp/new_secret.yaml
                  echo "✓ Created $SECRET_PATH"
                else
                  echo "❌ File not found: $SECRET_PATH"
                  echo ""
                  echo "Available secret files:"
                  if ls secrets/*.{yaml,yml,json} 2>/dev/null | head -5; then
                    echo ""
                  else
                    echo "  (none found)"
                    echo ""
                  fi
                  echo "Options:"
                  echo "  1. nix run .#secrets-edit -- --create $SECRET_FILE  # Create new file"
                  echo "  2. nix run .#secrets-edit -- [existing-file]        # Edit existing"
                  echo "  3. nix run .#secrets-init                           # Initialize setup"
                  exit 1
                fi
              fi

              # Verify file is encrypted
              if ! (grep -q 'ENC\[AES256_GCM,' "$SECRET_PATH" || (grep -q '^sops:' "$SECRET_PATH" && grep -q '^\s*mac:' "$SECRET_PATH")); then
                echo "⚠️  Warning: $SECRET_PATH appears to contain plaintext!"
                echo "   This should not happen in Secret-First mode."
                echo "   File will be encrypted after editing."
              fi

              echo "Opening $SECRET_PATH with SOPS editor..."
              ${pkgs.sops}/bin/sops edit "$SECRET_PATH"

              # Verify encryption after edit
              if grep -q 'ENC\[AES256_GCM,' "$SECRET_PATH" || (grep -q '^sops:' "$SECRET_PATH" && grep -q '^\s*mac:' "$SECRET_PATH"); then
                echo "✅ File saved and encrypted successfully"
              else
                echo "❌ Warning: File may not be properly encrypted!"
                echo "   Check your SOPS configuration and try again."
                exit 1
              fi
            ''}";
          };
        };
      }) // {
        # NixOS module (unchanged)
        nixosModules.default = import ./module.nix;
        
        # Templates from examples
        templates = {
          systemd = {
            path = ./examples/systemd-web-api;
            description = "SystemD service with sops-nix integration";
          };
          app = {
            path = ./examples/cli-tool;
            description = "Standalone CLI application with secrets";
          };
          script = {
            path = ./examples/deploy-script;
            description = "Encrypted shell script execution";
          };
          default = {
            path = ./examples/systemd-web-api;
            description = "SystemD service with sops-nix integration (default)";
          };
        };
      };
}
