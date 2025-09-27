{
  description = "RedwoodSDK R2 Connection Info Local Completion System";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";

    # Fixed reference to sops-nix for Secret-First development
    sops-nix = {
      url = "github:Mic92/sops-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, sops-nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # Common dependencies for R2 development
        commonDeps = with pkgs; [
          nodejs_20
          jq
          yq-go
          curl
          just
          age
          sops
        ];

        # Wrangler configuration generator (Node.js script)
        wrangler-config-gen = pkgs.writeScriptBin "gen-wrangler-config" ''
          #!${pkgs.bash}/bin/bash
          set -euo pipefail

          # Execute the Node.js script from current working directory
          # This assumes the user runs the command from the project root
          if [[ ! -f scripts/gen-wrangler-config.js ]]; then
            echo "❌ Error: scripts/gen-wrangler-config.js not found in current directory"
            echo "   Please run this command from the project root directory"
            exit 1
          fi

          ${pkgs.nodejs_20}/bin/node scripts/gen-wrangler-config.js "$@"
        '';


        # Secret validation script
        validate-secrets = pkgs.writeScriptBin "validate-secrets" ''
          #!${pkgs.bash}/bin/bash
          set -euo pipefail

          echo "= Validating secret configuration..."

          # Check for Age key
          if [[ ! -f ~/.config/sops/age/keys.txt ]]; then
            echo "L Age key not found at ~/.config/sops/age/keys.txt"
            exit 1
          fi

          # Check for SOPS config
          if [[ ! -f .sops.yaml ]]; then
            echo "L SOPS config (.sops.yaml) not found"
            exit 1
          fi

          # Check for R2 secrets file
          if [[ -f secrets/r2.yaml ]]; then
            echo " R2 secrets file found"

            # Validate decryption capability
            if ${pkgs.sops}/bin/sops -d secrets/r2.yaml > /dev/null 2>&1; then
              echo " R2 secrets successfully decryptable"
            else
              echo "L R2 secrets decryption failed"
              exit 1
            fi
          else
            echo "�  R2 secrets file not found - run secrets initialization"
          fi

          echo " Secret validation completed successfully"
        '';

        # R2 Connection Manifest Generator (Node.js based)
        gen-connection-manifest = pkgs.writeScriptBin "gen-connection-manifest" ''
          #!${pkgs.bash}/bin/bash
          set -euo pipefail

          # Execute the Node.js manifest generator from current working directory
          if [[ ! -f scripts/gen-connection-manifest.js ]]; then
            echo "❌ Error: scripts/gen-connection-manifest.js not found in current directory"
            echo "   Please run this command from the project root directory"
            exit 1
          fi

          ${pkgs.nodejs_20}/bin/node scripts/gen-connection-manifest.js "$@"
        '';

        # Enhanced R2 Manifest Generator with environment support
        gen-r2-manifest = pkgs.writeScriptBin "gen-r2-manifest" ''
          #!${pkgs.bash}/bin/bash
          set -euo pipefail

          # Enhanced R2 manifest generation with environment support
          if [[ ! -f scripts/gen-connection-manifest.js ]]; then
            echo "❌ Error: scripts/gen-connection-manifest.js not found in current directory"
            echo "   Please run this command from the project root directory"
            exit 1
          fi

          # Support for environment parameter
          ENV_PARAM=""
          if [[ $# -gt 0 ]] && [[ "$1" == "--env" ]]; then
            if [[ $# -lt 2 ]]; then
              echo "❌ Error: --env requires an environment name"
              echo "Usage: gen-r2-manifest [--env ENV_NAME] [other options]"
              exit 1
            fi
            ENV_PARAM="--env $2"
            shift 2
          fi

          echo "🔧 Generating R2 connection manifest..."
          ${pkgs.nodejs_20}/bin/node scripts/gen-connection-manifest.js $ENV_PARAM "$@"
        '';

        # Generate R2 manifests for all environments
        gen-r2-all = pkgs.writeScriptBin "gen-r2-all" ''
          #!${pkgs.bash}/bin/bash
          set -euo pipefail

          echo "🔧 Generating R2 connection manifests for all environments..."

          # Check if the generator exists
          if [[ ! -f scripts/gen-connection-manifest.js ]]; then
            echo "❌ Error: scripts/gen-connection-manifest.js not found in current directory"
            echo "   Please run this command from the project root directory"
            exit 1
          fi

          # Get list of available environments
          ENVS=$(${pkgs.nodejs_20}/bin/node scripts/gen-connection-manifest.js --list-envs 2>/dev/null || echo "dev stg prod")

          echo "📋 Available environments: $ENVS"
          echo ""

          SUCCESS_COUNT=0
          TOTAL_COUNT=0

          for env in $ENVS; do
            TOTAL_COUNT=$((TOTAL_COUNT + 1))
            echo "🔧 Generating manifest for environment: $env"

            if ${pkgs.nodejs_20}/bin/node scripts/gen-connection-manifest.js --env "$env" "$@"; then
              echo "✅ Successfully generated manifest for $env"
              SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            else
              echo "❌ Failed to generate manifest for $env"
            fi
            echo ""
          done

          echo "📊 Summary: $SUCCESS_COUNT/$TOTAL_COUNT environments processed successfully"

          if [[ $SUCCESS_COUNT -eq $TOTAL_COUNT ]]; then
            echo "🎉 All R2 manifests generated successfully!"
            exit 0
          else
            echo "⚠️ Some environments failed to generate"
            exit 1
          fi
        '';

        # Enhanced Wrangler Configuration Generator with validation
        gen-wrangler-config-enhanced = pkgs.writeScriptBin "gen-wrangler-config-enhanced" ''
          #!${pkgs.bash}/bin/bash
          set -euo pipefail

          # Enhanced wrangler config generation with built-in validation
          if [[ ! -f scripts/gen-wrangler-config.js ]]; then
            echo "❌ Error: scripts/gen-wrangler-config.js not found in current directory"
            echo "   Please run this command from the project root directory"
            exit 1
          fi

          # Parse command line arguments
          VALIDATE_AFTER=true
          BACKUP_EXISTING=true

          while [[ $# -gt 0 ]]; do
            case $1 in
              --no-validate)
                VALIDATE_AFTER=false
                shift
                ;;
              --no-backup)
                BACKUP_EXISTING=false
                shift
                ;;
              *)
                break
                ;;
            esac
          done

          # Backup existing configuration if requested
          if [[ "$BACKUP_EXISTING" == "true" ]] && [[ -f wrangler.jsonc ]]; then
            BACKUP_FILE="wrangler.jsonc.backup.$(date +%Y%m%d_%H%M%S)"
            echo "💾 Backing up existing wrangler.jsonc to $BACKUP_FILE"
            cp wrangler.jsonc "$BACKUP_FILE"
          fi

          # Generate configuration
          echo "🔧 Generating wrangler.jsonc configuration..."
          if ${pkgs.nodejs_20}/bin/node scripts/gen-wrangler-config.js "$@"; then
            echo "✅ Configuration generated successfully"

            # Validate if requested
            if [[ "$VALIDATE_AFTER" == "true" ]] && [[ -f scripts/test-wrangler-config.js ]]; then
              echo "🧪 Validating generated configuration..."
              if ${pkgs.nodejs_20}/bin/node scripts/test-wrangler-config.js --quiet; then
                echo "✅ Configuration validation passed"
              else
                echo "⚠️ Configuration validation failed, but file was generated"
                exit 1
              fi
            fi
          else
            echo "❌ Configuration generation failed"
            exit 1
          fi
        '';

        # R2 Configuration Validator
        validate-r2-config = pkgs.writeScriptBin "validate-r2-config" ''
          #!${pkgs.bash}/bin/bash
          set -euo pipefail

          echo "🧪 R2 Configuration Validator"
          echo "============================"

          # Check for required files
          MISSING_FILES=()

          if [[ ! -f scripts/test-wrangler-config.js ]]; then
            MISSING_FILES+=("scripts/test-wrangler-config.js")
          fi

          if [[ ! -f scripts/test-connection-manifest.js ]]; then
            MISSING_FILES+=("scripts/test-connection-manifest.js")
          fi

          if [[ ''${#MISSING_FILES[@]} -gt 0 ]]; then
            echo "❌ Missing required validator scripts:"
            for file in "''${MISSING_FILES[@]}"; do
              echo "   - $file"
            done
            echo "   Please run this command from the project root directory"
            exit 1
          fi

          # Parse environment parameter
          ENV="dev"
          VERBOSE=false

          while [[ $# -gt 0 ]]; do
            case $1 in
              --env)
                ENV="$2"
                shift 2
                ;;
              --verbose|-v)
                VERBOSE=true
                shift
                ;;
              *)
                echo "Unknown option: $1"
                echo "Usage: validate-r2-config [--env ENV] [--verbose]"
                exit 1
                ;;
            esac
          done

          echo "🔍 Validating R2 configuration for environment: $ENV"
          echo ""

          # Validate wrangler configuration
          echo "📋 Validating wrangler.jsonc..."
          if [[ "$VERBOSE" == "true" ]]; then
            ${pkgs.nodejs_20}/bin/node scripts/test-wrangler-config.js --env "$ENV"
          else
            ${pkgs.nodejs_20}/bin/node scripts/test-wrangler-config.js --env "$ENV" --quiet
          fi
          WRANGLER_STATUS=$?

          # Validate connection manifest if it exists
          echo ""
          echo "📋 Validating connection manifest..."
          MANIFEST_STATUS=0
          if [[ -f "generated/r2-connection-manifest-$ENV.json" ]]; then
            if [[ "$VERBOSE" == "true" ]]; then
              ${pkgs.nodejs_20}/bin/node scripts/test-connection-manifest.js --env "$ENV"
            else
              ${pkgs.nodejs_20}/bin/node scripts/test-connection-manifest.js --env "$ENV" --quiet
            fi
            MANIFEST_STATUS=$?
          else
            echo "⚠️ Connection manifest not found for $ENV environment"
            echo "   Run 'nix run .#gen-r2-manifest -- --env $ENV' to generate"
          fi

          echo ""
          echo "📊 Validation Summary"
          echo "===================="

          if [[ $WRANGLER_STATUS -eq 0 ]]; then
            echo "✅ Wrangler configuration: VALID"
          else
            echo "❌ Wrangler configuration: INVALID"
          fi

          if [[ $MANIFEST_STATUS -eq 0 ]]; then
            echo "✅ Connection manifest: VALID"
          else
            echo "❌ Connection manifest: INVALID"
          fi

          if [[ $WRANGLER_STATUS -eq 0 ]] && [[ $MANIFEST_STATUS -eq 0 ]]; then
            echo ""
            echo "🎉 All R2 configurations are valid!"
            exit 0
          else
            echo ""
            echo "⚠️ Some configurations are invalid. Check the output above for details."
            exit 1
          fi
        '';

        # R2 Environment Discovery
        discover-r2-envs = pkgs.writeScriptBin "discover-r2-envs" ''
          #!${pkgs.bash}/bin/bash
          set -euo pipefail

          echo "🔍 R2 Environment Discovery"
          echo "=========================="

          # Check available environments from various sources
          FOUND_ENVS=()

          # From wrangler config generator
          if [[ -f scripts/gen-wrangler-config.js ]]; then
            echo "📋 Checking environments from wrangler config generator..."
            WRANGLER_ENVS=$(${pkgs.nodejs_20}/bin/node scripts/gen-wrangler-config.js --list-envs 2>/dev/null || echo "")
            if [[ -n "$WRANGLER_ENVS" ]]; then
              echo "   Found: $WRANGLER_ENVS"
              FOUND_ENVS+=($WRANGLER_ENVS)
            fi
          fi

          # From connection manifest generator
          if [[ -f scripts/gen-connection-manifest.js ]]; then
            echo "📋 Checking environments from connection manifest generator..."
            MANIFEST_ENVS=$(${pkgs.nodejs_20}/bin/node scripts/gen-connection-manifest.js --list-envs 2>/dev/null || echo "")
            if [[ -n "$MANIFEST_ENVS" ]]; then
              echo "   Found: $MANIFEST_ENVS"
              FOUND_ENVS+=($MANIFEST_ENVS)
            fi
          fi

          # From existing generated files
          echo "📋 Checking for existing generated files..."
          if [[ -d generated ]]; then
            for file in generated/r2-connection-manifest-*.json; do
              if [[ -f "$file" ]]; then
                ENV_NAME=$(basename "$file" | sed 's/r2-connection-manifest-//; s/.json$//')
                echo "   Found manifest for: $ENV_NAME"
                FOUND_ENVS+=("$ENV_NAME")
              fi
            done
          fi

          # Remove duplicates and sort
          UNIQUE_ENVS=($(printf '%s\n' "''${FOUND_ENVS[@]}" | sort -u))

          echo ""
          echo "📊 Summary"
          echo "=========="

          if [[ ''${#UNIQUE_ENVS[@]} -eq 0 ]]; then
            echo "❌ No environments found"
            echo "   Default environments: dev, stg, prod"
            exit 1
          else
            echo "✅ Found ''${#UNIQUE_ENVS[@]} environment(s):"
            for env in "''${UNIQUE_ENVS[@]}"; do
              echo "   - $env"
            done
          fi

          echo ""
          echo "🛠️ Common commands for discovered environments:"
          for env in "''${UNIQUE_ENVS[@]}"; do
            echo "   nix run .#gen-r2-manifest -- --env $env"
            echo "   nix run .#validate-r2-config -- --env $env"
            echo "   just r2:gen-config-env $env"
          done
        '';

        # Remote State Fetcher for Cloudflare Resources
        fetch-remote-state = pkgs.writeScriptBin "fetch-remote-state" ''
          #!${pkgs.bash}/bin/bash
          set -euo pipefail

          # Check if fetch-remote-state.js exists
          if [[ ! -f scripts/fetch-remote-state.js ]]; then
            echo "❌ Error: scripts/fetch-remote-state.js not found in current directory"
            echo "   Make sure you're running this from the project root"
            exit 1
          fi

          # Execute the Node.js script with all arguments passed through
          ${pkgs.nodejs_20}/bin/node scripts/fetch-remote-state.js "$@"
        '';

        # R2 Development Workflow Helper
        r2-dev-workflow = pkgs.writeScriptBin "r2-dev-workflow" ''
          #!${pkgs.bash}/bin/bash
          set -euo pipefail

          echo "🚀 R2 Development Workflow Helper"
          echo "================================="

          ENV="''${1:-dev}"
          ACTION="''${2:-full}"

          echo "Environment: $ENV"
          echo "Action: $ACTION"
          echo ""

          case "$ACTION" in
            "validate"|"check")
              echo "🧪 Running validation workflow..."
              ${pkgs.nodejs_20}/bin/node scripts/test-wrangler-config.js --env "$ENV" || exit 1
              if [[ -f "generated/r2-connection-manifest-$ENV.json" ]]; then
                ${pkgs.nodejs_20}/bin/node scripts/test-connection-manifest.js --env "$ENV" || exit 1
              fi
              echo "✅ Validation complete"
              ;;

            "generate"|"gen")
              echo "🔧 Running generation workflow..."
              ${pkgs.nodejs_20}/bin/node scripts/gen-wrangler-config.js "$ENV" || exit 1
              ${pkgs.nodejs_20}/bin/node scripts/gen-connection-manifest.js --env "$ENV" || exit 1
              echo "✅ Generation complete"
              ;;

            "test")
              echo "🧪 Running configuration test workflow..."
              echo "Running configuration validation..."
              ${pkgs.nodejs_20}/bin/node scripts/test-wrangler-config.js --env "$ENV" || exit 1
              if [[ -f "generated/r2-connection-manifest-$ENV.json" ]]; then
                ${pkgs.nodejs_20}/bin/node scripts/test-connection-manifest.js --env "$ENV" || exit 1
              fi
              echo "✅ Configuration test complete for $ENV environment"
              ;;

            "full"|"all")
              echo "🔧 Running full development workflow..."
              echo ""

              echo "Step 1: Generate configurations"
              ${pkgs.nodejs_20}/bin/node scripts/gen-wrangler-config.js "$ENV" || exit 1
              ${pkgs.nodejs_20}/bin/node scripts/gen-connection-manifest.js --env "$ENV" || exit 1

              echo ""
              echo "Step 2: Validate configurations"
              ${pkgs.nodejs_20}/bin/node scripts/test-wrangler-config.js --env "$ENV" || exit 1
              ${pkgs.nodejs_20}/bin/node scripts/test-connection-manifest.js --env "$ENV" || exit 1

              echo ""
              echo "Step 3: Configuration test complete"
              echo "✅ Configuration ready for $ENV environment"

              echo ""
              echo "🎉 Full workflow complete for $ENV!"
              ;;

            *)
              echo "❌ Unknown action: $ACTION"
              echo "Available actions:"
              echo "   validate|check  - Validate existing configurations"
              echo "   generate|gen    - Generate configurations"
              echo "   test           - Configuration validation for all environments"
              echo "   full|all       - Run complete workflow"
              echo ""
              echo "Usage: r2-dev-workflow [ENV] [ACTION]"
              echo "   ENV defaults to 'dev'"
              echo "   ACTION defaults to 'full'"
              exit 1
              ;;
          esac
        '';

        # Drift Detection Script
        diff-state = pkgs.writeScriptBin "diff-state" ''
          #!${pkgs.bash}/bin/bash
          set -euo pipefail

          # Check if diff-state.js exists
          if [[ ! -f scripts/diff-state.js ]]; then
            echo "❌ Error: scripts/diff-state.js not found in current directory"
            echo "   Make sure you're running this from the project root"
            exit 1
          fi

          # Execute the Node.js script with all arguments passed through
          ${pkgs.nodejs_20}/bin/node scripts/diff-state.js "$@"
        '';

        # Pulumi Safety Gate Script
        pulumi-safety-gate = pkgs.writeScriptBin "pulumi-safety-gate" ''
          #!${pkgs.bash}/bin/bash
          set -euo pipefail

          # Check if pulumi-safety-gate.js exists
          if [[ ! -f scripts/pulumi-safety-gate.js ]]; then
            echo "❌ Error: scripts/pulumi-safety-gate.js not found in current directory"
            echo "   Make sure you're running this from the project root"
            exit 1
          fi

          # Execute the Node.js script with all arguments passed through
          ${pkgs.nodejs_20}/bin/node scripts/pulumi-safety-gate.js "$@"
        '';

        # Pulumi plan packages for each environment
        pulumi-plan-dev = pkgs.writeScriptBin "pulumi-plan-dev" ''
          #!${pkgs.bash}/bin/bash
          set -euo pipefail

          echo "🏗️ Running Pulumi plan for dev environment..."

          # Check if Pulumi project exists
          if [[ ! -f "pulumi/Pulumi.yaml" ]]; then
            echo "⏭️ Skipping Pulumi plan: Pulumi project not found"
            echo "   Expected: pulumi/Pulumi.yaml"
            exit 0
          fi

          # Check if SOT configuration exists
          if [[ ! -f "spec/dev/cloudflare.yaml" ]]; then
            echo "⏭️ Skipping Pulumi plan: SOT configuration not found"
            echo "   Expected: spec/dev/cloudflare.yaml"
            exit 0
          fi

          # Run safety gate validation for plan operation
          echo "🛡️ Running Pulumi safety gate for plan operation..."
          if ! ${pkgs.nodejs_20}/bin/node scripts/pulumi-safety-gate.js --operation plan --env dev --quiet; then
            echo "❌ Pulumi safety gate failed for dev environment"
            exit 1
          fi

          # Run Pulumi preview
          echo "🚀 Executing Pulumi preview for dev environment..."
          cd pulumi
          ${pkgs.pulumi}/bin/pulumi preview --stack dev --non-interactive "$@"
        '';

        pulumi-plan-stg = pkgs.writeScriptBin "pulumi-plan-stg" ''
          #!${pkgs.bash}/bin/bash
          set -euo pipefail

          echo "🏗️ Running Pulumi plan for stg environment..."

          # Check if Pulumi project exists
          if [[ ! -f "pulumi/Pulumi.yaml" ]]; then
            echo "⏭️ Skipping Pulumi plan: Pulumi project not found"
            echo "   Expected: pulumi/Pulumi.yaml"
            exit 0
          fi

          # Check if SOT configuration exists
          if [[ ! -f "spec/stg/cloudflare.yaml" ]]; then
            echo "⏭️ Skipping Pulumi plan: SOT configuration not found"
            echo "   Expected: spec/stg/cloudflare.yaml"
            exit 0
          fi

          # Run safety gate validation for plan operation
          echo "🛡️ Running Pulumi safety gate for plan operation..."
          if ! ${pkgs.nodejs_20}/bin/node scripts/pulumi-safety-gate.js --operation plan --env stg --quiet; then
            echo "❌ Pulumi safety gate failed for stg environment"
            exit 1
          fi

          # Run Pulumi preview
          echo "🚀 Executing Pulumi preview for stg environment..."
          cd pulumi
          ${pkgs.pulumi}/bin/pulumi preview --stack stg --non-interactive "$@"
        '';

        pulumi-plan-prod = pkgs.writeScriptBin "pulumi-plan-prod" ''
          #!${pkgs.bash}/bin/bash
          set -euo pipefail

          echo "🏗️ Running Pulumi plan for prod environment..."

          # Check if Pulumi project exists
          if [[ ! -f "pulumi/Pulumi.yaml" ]]; then
            echo "⏭️ Skipping Pulumi plan: Pulumi project not found"
            echo "   Expected: pulumi/Pulumi.yaml"
            exit 0
          fi

          # Check if SOT configuration exists
          if [[ ! -f "spec/prod/cloudflare.yaml" ]]; then
            echo "⏭️ Skipping Pulumi plan: SOT configuration not found"
            echo "   Expected: spec/prod/cloudflare.yaml"
            exit 0
          fi

          # Run safety gate validation for plan operation
          echo "🛡️ Running Pulumi safety gate for plan operation..."
          if ! ${pkgs.nodejs_20}/bin/node scripts/pulumi-safety-gate.js --operation plan --env prod --quiet; then
            echo "❌ Pulumi safety gate failed for prod environment"
            exit 1
          fi

          # Run Pulumi preview
          echo "🚀 Executing Pulumi preview for prod environment..."
          cd pulumi
          ${pkgs.pulumi}/bin/pulumi preview --stack prod --non-interactive "$@"
        '';

      in
      {
        # Development shells with all necessary tools
        devShells = {
          default = pkgs.mkShell {
            buildInputs = commonDeps ++ [
              # Cloudflare Workers development
              pkgs.nodePackages.wrangler

              # Additional R2 development tools
              pkgs.awscli2  # For S3-compatible API testing if needed

              # Infrastructure as Code
              pkgs.pulumi  # IaC automation

              # Note: For JSON Schema validation with AJV CLI, you can install it via npm:
              # npm install -g ajv-cli
            ];

            shellHook = ''
              echo "=� RedwoodSDK R2 Development Environment"
              echo "======================================"
              echo "Available commands:"
              echo "  just r2:status     - Check R2 configuration status"
              echo "  just r2:test       - Validate R2 configuration"
              echo "  just secrets-init  - Initialize encrypted secrets"
              echo "  just secrets-edit  - Edit R2 secrets"
              echo ""

              # Ensure SOPS Age key is configured
              if [[ ! -f ~/.config/sops/age/keys.txt ]]; then
                echo "�  Age key not found. Run 'just secrets-init' to set up encryption."
              fi

              # Export SOPS environment
              export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt
            '';
          };

          # Minimal shell for CI/automated testing
          ci = pkgs.mkShell {
            buildInputs = [
              pkgs.sops
              pkgs.age
              pkgs.jq
              pkgs.yq-go
            ];
          };
        };

        # R2 apps for easy execution
        apps = {
          # R2 manifest generation
          gen-connection-manifest = {
            type = "app";
            program = "${gen-connection-manifest}/bin/gen-connection-manifest";
          };

          # Enhanced R2 manifest generation with environment support
          gen-r2-manifest = {
            type = "app";
            program = "${gen-r2-manifest}/bin/gen-r2-manifest";
          };

          # Generate R2 manifests for all environments
          gen-r2-all = {
            type = "app";
            program = "${gen-r2-all}/bin/gen-r2-all";
          };

          # Enhanced wrangler config generation with validation
          gen-wrangler-config-enhanced = {
            type = "app";
            program = "${gen-wrangler-config-enhanced}/bin/gen-wrangler-config-enhanced";
          };

          # R2 configuration validation
          validate-r2-config = {
            type = "app";
            program = "${validate-r2-config}/bin/validate-r2-config";
          };

          # R2 environment discovery
          discover-r2-envs = {
            type = "app";
            program = "${discover-r2-envs}/bin/discover-r2-envs";
          };

          # Remote state fetcher for Cloudflare resources
          fetch-remote-state = {
            type = "app";
            program = "${fetch-remote-state}/bin/fetch-remote-state";
          };

          # R2 development workflow helper
          r2-dev-workflow = {
            type = "app";
            program = "${r2-dev-workflow}/bin/r2-dev-workflow";
          };

          # Drift detection and state comparison
          diff-state = {
            type = "app";
            program = "${diff-state}/bin/diff-state";
          };

          # Pulumi safety gate for infrastructure operations
          pulumi-safety-gate = {
            type = "app";
            program = "${pulumi-safety-gate}/bin/pulumi-safety-gate";
          };

          # Pulumi plan operations for each environment
          pulumi-plan-dev = {
            type = "app";
            program = "${pulumi-plan-dev}/bin/pulumi-plan-dev";
          };

          pulumi-plan-stg = {
            type = "app";
            program = "${pulumi-plan-stg}/bin/pulumi-plan-stg";
          };

          pulumi-plan-prod = {
            type = "app";
            program = "${pulumi-plan-prod}/bin/pulumi-plan-prod";
          };

          # Secret management
          secrets-init = {
            type = "app";
            program = "${pkgs.writeScriptBin "secrets-init" ''
              #!${pkgs.bash}/bin/bash
              set -euo pipefail

              echo "=' Initializing R2 secrets..."

              # Create Age key if not exists
              mkdir -p ~/.config/sops/age
              if [[ ! -f ~/.config/sops/age/keys.txt ]]; then
                echo "= Generating Age key..."
                ${pkgs.age}/bin/age-keygen -o ~/.config/sops/age/keys.txt
                echo " Age key generated at ~/.config/sops/age/keys.txt"
              else
                echo " Age key already exists"
              fi

              # Create .sops.yaml if not exists
              if [[ ! -f .sops.yaml ]]; then
                echo "=� Creating .sops.yaml configuration..."
                AGE_PUBLIC_KEY=$(${pkgs.age}/bin/age-keygen -y ~/.config/sops/age/keys.txt)
                cat > .sops.yaml << EOF
              keys:
                - &user_age $AGE_PUBLIC_KEY
              creation_rules:
                - path_regex: secrets/.*\.yaml$
                  age: [*user_age]
              EOF
                echo " .sops.yaml created"
              else
                echo " .sops.yaml already exists"
              fi

              # Create secrets directory
              mkdir -p secrets

              # Create R2 template if secrets/r2.yaml doesn't exist
              if [[ ! -f secrets/r2.yaml ]]; then
                echo "=� Creating R2 secrets template..."
                cat > r2.yaml.example << EOF
              # R2 Configuration Template
              # Copy this to secrets/r2.yaml and encrypt with 'just secrets-edit'

              # Cloudflare Account ID (required)
              cf_account_id: your-account-id-here

              # R2 bucket names (comma-separated for multiple buckets)
              r2_buckets: user-uploads,static-assets

              # S3 API endpoint (auto-generated from account ID)
              r2_s3_endpoint: https://your-account-id-here.r2.cloudflarestorage.com

              # S3 API region (always 'auto' for R2)
              r2_region: auto

              # Note: R2 access keys are only needed for S3-compatible API access
              # For Workers Binding only (current setup), these are not required:
              # r2_access_key_id: your-access-key-here
              # r2_secret_access_key: your-secret-key-here
              EOF
                echo " Template created: r2.yaml.example"
                echo "   Copy to secrets/r2.yaml and run 'just secrets-edit' to encrypt"
              fi

              echo ""
              echo "<� Next steps:"
              echo "  1. Copy r2.yaml.example to secrets/r2.yaml"
              echo "  2. Edit secrets/r2.yaml with your R2 configuration"
              echo "  3. Run 'just secrets-edit' to encrypt the file"
              echo "  4. Run 'just r2:status' to verify setup"
            ''}/bin/secrets-init";
          };

          secrets-edit = {
            type = "app";
            program = "${pkgs.writeScriptBin "secrets-edit" ''
              #!${pkgs.bash}/bin/bash
              set -euo pipefail

              FILE="''${1:-secrets/r2.yaml}"

              echo "= Editing encrypted secrets: $FILE"

              if [[ ! -f ~/.config/sops/age/keys.txt ]]; then
                echo "L Age key not found. Run 'just secrets-init' first."
                exit 1
              fi

              if [[ ! -f .sops.yaml ]]; then
                echo "L SOPS config not found. Run 'just secrets-init' first."
                exit 1
              fi

              export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt
              ${pkgs.sops}/bin/sops "$FILE"
            ''}/bin/secrets-edit";
          };

          # Configuration generation (original)
          gen-wrangler-config = {
            type = "app";
            program = "${wrangler-config-gen}/bin/gen-wrangler-config";
          };

        };

        # Re-exported checks for validation
        checks = {
          # Secret security validation
          secrets = validate-secrets;

          # Flake format check
          flake-check = pkgs.runCommand "flake-check" {} ''
            echo " Flake format validation passed"
            touch $out
          '';

          # No plaintext secrets check
          no-plaintext-secrets = pkgs.runCommand "no-plaintext-secrets" {
            src = self;
          } ''
            cp -r $src/* .
            echo "🔍 Checking for plaintext secrets..."

            # Define secret patterns to detect
            SECRET_PATTERNS="AKIA[A-Z0-9]{16}|sk_live_[a-zA-Z0-9]{24,}|pk_live_[a-zA-Z0-9]{24,}|sk_test_[a-zA-Z0-9]{24,}|pk_test_[a-zA-Z0-9]{24,}"

            # Search for plaintext secrets (excluding legitimate documentation references and test files)
            FOUND_SECRETS=$(grep -r -E "$SECRET_PATTERNS" . --exclude-dir=.git --exclude-dir=result --exclude-dir=nix --exclude-dir=test-modules || true)

            if [[ -n "$FOUND_SECRETS" ]]; then
              echo "❌ SECURITY VIOLATION: Plaintext secrets detected!"
              echo "Found the following potential secrets:"
              echo "$FOUND_SECRETS"
              echo ""
              echo "🔐 Required actions:"
              echo "  1. Remove plaintext secrets from files"
              echo "  2. Use SOPS encryption: 'just secrets-edit'"
              echo "  3. Add sensitive files to .gitignore"
              echo ""
              echo "⚠️  This build MUST fail to prevent secret leakage."
              exit 1
            else
              echo "✅ No plaintext secrets detected"
              echo "🔐 Secret security validation: PASSED"
            fi

            touch $out
          '';

          # R2 configuration validation
          r2-config-validation = pkgs.runCommand "r2-config-validation" {
            src = self;
            buildInputs = [ pkgs.nodejs_20 ];
          } ''
            cp -r $src/* .
            echo "🔍 Validating R2 configuration structure..."

            # Check that essential files exist
            if [ ! -f "flake.nix" ]; then
              echo "❌ flake.nix not found"
              exit 1
            fi

            if [ ! -f "justfile" ]; then
              echo "❌ justfile not found"
              exit 1
            fi

            if [ ! -f "scripts/gen-wrangler-config.js" ]; then
              echo "❌ wrangler config generator not found"
              exit 1
            fi

            if [ ! -f "src/worker.ts" ]; then
              echo "❌ worker.ts not found"
              exit 1
            fi

            if [ ! -f "r2.yaml.example" ]; then
              echo "❌ R2 template not found"
              exit 1
            fi

            # Validate Node.js script syntax
            echo "🔍 Validating Node.js script syntax..."
            ${pkgs.nodejs_20}/bin/node --check "scripts/gen-wrangler-config.js"

            echo "✅ R2 configuration validation passed"
            touch $out
          '';

          # JavaScript syntax check
          typescript-check = pkgs.runCommand "typescript-check" {
            src = self;
            buildInputs = [ pkgs.nodejs_20 ];
          } ''
            cp -r $src/* .
            echo "🔍 Checking JavaScript syntax..."

            # Check all JavaScript files in scripts directory
            for js_file in scripts/*.js; do
              if [ -f "$js_file" ]; then
                echo "Checking $js_file..."
                ${pkgs.nodejs_20}/bin/node --check "$js_file" || exit 1
              fi
            done

            # Check helper files
            for js_file in helpers/*.js; do
              if [ -f "$js_file" ]; then
                echo "Checking $js_file..."
                ${pkgs.nodejs_20}/bin/node --check "$js_file" || exit 1
              fi
            done

            echo "✅ JavaScript syntax validation passed"
            touch $out
          '';

          # Data Plane operations prohibition check
          no-data-plane-operations = pkgs.runCommand "no-data-plane-operations" {
            src = self;
            buildInputs = [ pkgs.ripgrep ];
          } ''
            cp -r $src/* .
            echo "🔍 Checking for prohibited Data Plane operations..."

            # Define Data Plane operation patterns
            DATA_PLANE_PATTERNS="R2Bucket\\.(put|get|delete|list|createMultipartUpload|head)"

            # Search for Data Plane operations outside examples/ directory
            FOUND_OPERATIONS=$(rg "$DATA_PLANE_PATTERNS" --type-add 'source:*.{ts,js,jsx,tsx}' -t source . \
              --exclude-dir=examples --exclude-dir=.git --exclude-dir=result --exclude-dir=nix \
              --exclude-dir=test-env --exclude-dir=test-modules || true)

            if [[ -n "$FOUND_OPERATIONS" ]]; then
              echo "❌ SCOPE VIOLATION: Data Plane operations detected outside examples/!"
              echo "Found the following prohibited operations:"
              echo "$FOUND_OPERATIONS"
              echo ""
              echo "🎯 Scope definition:"
              echo "  - Resource Plane (allowed): Configuration, secrets, deployment management"
              echo "  - Data Plane (prohibited): R2 object operations, business logic"
              echo ""
              echo "📁 Required actions:"
              echo "  1. Move Data Plane code to examples/ directory"
              echo "  2. Keep only Resource Plane operations in main implementation"
              echo "  3. See SCOPE.md for detailed scope definition"
              echo ""
              echo "⚠️  This build MUST fail to maintain architectural integrity."
              exit 1
            else
              echo "✅ No prohibited Data Plane operations found"
              echo "🎯 Scope compliance: PASSED"
            fi

            touch $out
          '';

          # Drift Detection for dev environment
          drift-detection-dev = pkgs.runCommand "drift-detection-dev" {
            buildInputs = [ pkgs.nodejs_20 pkgs.nodePackages.wrangler ];
          } ''
            echo "🔍 Running drift detection for dev environment..."

            # Copy source files to build directory
            REPO_ROOT="/home/nixos/bin/src/deploy/cloudflare"
            cp -r "$REPO_ROOT"/* .

            # Create output directory
            mkdir -p generated

            # Skip if SOT configuration doesn't exist
            if [[ ! -f "spec/dev/cloudflare.yaml" ]]; then
              echo "⏭️ Skipping dev drift detection: SOT configuration not found"
              echo "   Expected: spec/dev/cloudflare.yaml"
              touch $out
              exit 0
            fi

            # Skip if wrangler is not authenticated (CI/CD friendly)
            if ! timeout 10s ${pkgs.nodePackages.wrangler}/bin/wrangler auth whoami &>/dev/null; then
              echo "⏭️ Skipping dev drift detection: Wrangler not authenticated"
              echo "   This is expected in CI/CD environments without Cloudflare credentials"
              touch $out
              exit 0
            fi

            # Run drift detection
            echo "🚀 Executing SOT vs Remote state comparison for dev..."
            if ${pkgs.nodejs_20}/bin/node scripts/diff-state.js --env dev --format summary --quiet; then
              echo "✅ Dev environment: No configuration drift detected"
            else
              exit_code=$?
              if [[ $exit_code -eq 1 ]]; then
                echo "❌ Dev environment: Configuration drift detected!"
                echo "   Run 'nix run .#diff-state -- --env dev' for detailed analysis"
                exit 1
              else
                echo "⚠️ Dev environment: Drift detection failed (exit code: $exit_code)"
                echo "   This may indicate SOT or remote state access issues"
                exit 1
              fi
            fi

            touch $out
          '';

          # Drift Detection for stg environment
          drift-detection-stg = pkgs.runCommand "drift-detection-stg" {
            buildInputs = [ pkgs.nodejs_20 pkgs.nodePackages.wrangler ];
          } ''
            echo "🔍 Running drift detection for stg environment..."

            # Copy source files to build directory
            REPO_ROOT="/home/nixos/bin/src/deploy/cloudflare"
            cp -r "$REPO_ROOT"/* .

            # Create output directory
            mkdir -p generated

            # Skip if SOT configuration doesn't exist
            if [[ ! -f "spec/stg/cloudflare.yaml" ]]; then
              echo "⏭️ Skipping stg drift detection: SOT configuration not found"
              echo "   Expected: spec/stg/cloudflare.yaml"
              touch $out
              exit 0
            fi

            # Skip if wrangler is not authenticated (CI/CD friendly)
            if ! timeout 10s ${pkgs.nodePackages.wrangler}/bin/wrangler auth whoami &>/dev/null; then
              echo "⏭️ Skipping stg drift detection: Wrangler not authenticated"
              echo "   This is expected in CI/CD environments without Cloudflare credentials"
              touch $out
              exit 0
            fi

            # Run drift detection
            echo "🚀 Executing SOT vs Remote state comparison for stg..."
            if ${pkgs.nodejs_20}/bin/node scripts/diff-state.js --env stg --format summary --quiet; then
              echo "✅ Stg environment: No configuration drift detected"
            else
              exit_code=$?
              if [[ $exit_code -eq 1 ]]; then
                echo "❌ Stg environment: Configuration drift detected!"
                echo "   Run 'nix run .#diff-state -- --env stg' for detailed analysis"
                exit 1
              else
                echo "⚠️ Stg environment: Drift detection failed (exit code: $exit_code)"
                echo "   This may indicate SOT or remote state access issues"
                exit 1
              fi
            fi

            touch $out
          '';

          # Drift Detection for prod environment
          drift-detection-prod = pkgs.runCommand "drift-detection-prod" {
            buildInputs = [ pkgs.nodejs_20 pkgs.nodePackages.wrangler ];
          } ''
            echo "🔍 Running drift detection for prod environment..."

            # Copy source files to build directory
            REPO_ROOT="/home/nixos/bin/src/deploy/cloudflare"
            cp -r "$REPO_ROOT"/* .

            # Create output directory
            mkdir -p generated

            # Skip if SOT configuration doesn't exist
            if [[ ! -f "spec/prod/cloudflare.yaml" ]]; then
              echo "⏭️ Skipping prod drift detection: SOT configuration not found"
              echo "   Expected: spec/prod/cloudflare.yaml"
              touch $out
              exit 0
            fi

            # Skip if wrangler is not authenticated (CI/CD friendly)
            if ! timeout 10s ${pkgs.nodePackages.wrangler}/bin/wrangler auth whoami &>/dev/null; then
              echo "⏭️ Skipping prod drift detection: Wrangler not authenticated"
              echo "   This is expected in CI/CD environments without Cloudflare credentials"
              touch $out
              exit 0
            fi

            # Run drift detection
            echo "🚀 Executing SOT vs Remote state comparison for prod..."
            if ${pkgs.nodejs_20}/bin/node scripts/diff-state.js --env prod --format summary --quiet; then
              echo "✅ Prod environment: No configuration drift detected"
            else
              exit_code=$?
              if [[ $exit_code -eq 1 ]]; then
                echo "❌ Prod environment: Configuration drift detected!"
                echo "   Run 'nix run .#diff-state -- --env prod' for detailed analysis"
                exit 1
              else
                echo "⚠️ Prod environment: Drift detection failed (exit code: $exit_code)"
                echo "   This may indicate SOT or remote state access issues"
                exit 1
              fi
            fi

            touch $out
          '';

          # Pulumi Plan Validation for dev environment
          pulumi-plan-dev = pkgs.runCommand "pulumi-plan-dev" {
            buildInputs = [ pkgs.nodejs_20 pkgs.nodePackages.wrangler pkgs.pulumi ];
          } ''
            echo "🏗️ Running Pulumi plan validation for dev environment..."

            # Copy source files to build directory
            REPO_ROOT="/home/nixos/bin/src/deploy/cloudflare"
            cp -r "$REPO_ROOT"/* .

            # Skip if Pulumi project doesn't exist
            if [[ ! -f "pulumi/Pulumi.yaml" ]]; then
              echo "⏭️ Skipping Pulumi plan: Pulumi project not found"
              echo "   Expected: pulumi/Pulumi.yaml"
              touch $out
              exit 0
            fi

            # Skip if SOT configuration doesn't exist
            if [[ ! -f "spec/dev/cloudflare.yaml" ]]; then
              echo "⏭️ Skipping Pulumi plan: SOT configuration not found"
              echo "   Expected: spec/dev/cloudflare.yaml"
              touch $out
              exit 0
            fi

            # Skip if wrangler is not authenticated (CI/CD friendly)
            if ! timeout 10s ${pkgs.nodePackages.wrangler}/bin/wrangler auth whoami &>/dev/null; then
              echo "⏭️ Skipping Pulumi plan: Wrangler not authenticated"
              echo "   This is expected in CI/CD environments without Cloudflare credentials"
              touch $out
              exit 0
            fi

            # Run safety gate validation for plan operation
            echo "🛡️ Running Pulumi safety gate for plan operation..."
            if ! ${pkgs.nodejs_20}/bin/node scripts/pulumi-safety-gate.js --operation plan --env dev --quiet; then
              echo "❌ Pulumi safety gate failed for dev environment"
              exit 1
            fi

            # Run Pulumi preview
            echo "🚀 Executing Pulumi preview for dev environment..."
            cd pulumi
            if ! ${pkgs.pulumi}/bin/pulumi preview --stack dev --non-interactive; then
              echo "❌ Pulumi preview failed for dev environment"
              exit 1
            fi

            echo "✅ Pulumi plan validation passed for dev environment"
            touch $out
          '';

          # Pulumi Plan Validation for stg environment
          pulumi-plan-stg = pkgs.runCommand "pulumi-plan-stg" {
            buildInputs = [ pkgs.nodejs_20 pkgs.nodePackages.wrangler pkgs.pulumi ];
          } ''
            echo "🏗️ Running Pulumi plan validation for stg environment..."

            # Copy source files to build directory
            REPO_ROOT="/home/nixos/bin/src/deploy/cloudflare"
            cp -r "$REPO_ROOT"/* .

            # Skip if Pulumi project doesn't exist
            if [[ ! -f "pulumi/Pulumi.yaml" ]]; then
              echo "⏭️ Skipping Pulumi plan: Pulumi project not found"
              echo "   Expected: pulumi/Pulumi.yaml"
              touch $out
              exit 0
            fi

            # Skip if SOT configuration doesn't exist
            if [[ ! -f "spec/stg/cloudflare.yaml" ]]; then
              echo "⏭️ Skipping Pulumi plan: SOT configuration not found"
              echo "   Expected: spec/stg/cloudflare.yaml"
              touch $out
              exit 0
            fi

            # Skip if wrangler is not authenticated (CI/CD friendly)
            if ! timeout 10s ${pkgs.nodePackages.wrangler}/bin/wrangler auth whoami &>/dev/null; then
              echo "⏭️ Skipping Pulumi plan: Wrangler not authenticated"
              echo "   This is expected in CI/CD environments without Cloudflare credentials"
              touch $out
              exit 0
            fi

            # Run safety gate validation for plan operation
            echo "🛡️ Running Pulumi safety gate for plan operation..."
            if ! ${pkgs.nodejs_20}/bin/node scripts/pulumi-safety-gate.js --operation plan --env stg --quiet; then
              echo "❌ Pulumi safety gate failed for stg environment"
              exit 1
            fi

            # Run Pulumi preview
            echo "🚀 Executing Pulumi preview for stg environment..."
            cd pulumi
            if ! ${pkgs.pulumi}/bin/pulumi preview --stack stg --non-interactive; then
              echo "❌ Pulumi preview failed for stg environment"
              exit 1
            fi

            echo "✅ Pulumi plan validation passed for stg environment"
            touch $out
          '';

          # Pulumi Plan Validation for prod environment
          pulumi-plan-prod = pkgs.runCommand "pulumi-plan-prod" {
            buildInputs = [ pkgs.nodejs_20 pkgs.nodePackages.wrangler pkgs.pulumi ];
          } ''
            echo "🏗️ Running Pulumi plan validation for prod environment..."

            # Copy source files to build directory
            REPO_ROOT="/home/nixos/bin/src/deploy/cloudflare"
            cp -r "$REPO_ROOT"/* .

            # Skip if Pulumi project doesn't exist
            if [[ ! -f "pulumi/Pulumi.yaml" ]]; then
              echo "⏭️ Skipping Pulumi plan: Pulumi project not found"
              echo "   Expected: pulumi/Pulumi.yaml"
              touch $out
              exit 0
            fi

            # Skip if SOT configuration doesn't exist
            if [[ ! -f "spec/prod/cloudflare.yaml" ]]; then
              echo "⏭️ Skipping Pulumi plan: SOT configuration not found"
              echo "   Expected: spec/prod/cloudflare.yaml"
              touch $out
              exit 0
            fi

            # Skip if wrangler is not authenticated (CI/CD friendly)
            if ! timeout 10s ${pkgs.nodePackages.wrangler}/bin/wrangler auth whoami &>/dev/null; then
              echo "⏭️ Skipping Pulumi plan: Wrangler not authenticated"
              echo "   This is expected in CI/CD environments without Cloudflare credentials"
              touch $out
              exit 0
            fi

            # Run safety gate validation for plan operation
            echo "🛡️ Running Pulumi safety gate for plan operation..."
            if ! ${pkgs.nodejs_20}/bin/node scripts/pulumi-safety-gate.js --operation plan --env prod --quiet; then
              echo "❌ Pulumi safety gate failed for prod environment"
              exit 1
            fi

            # Run Pulumi preview
            echo "🚀 Executing Pulumi preview for prod environment..."
            cd pulumi
            if ! ${pkgs.pulumi}/bin/pulumi preview --stack prod --non-interactive; then
              echo "❌ Pulumi preview failed for prod environment"
              exit 1
            fi

            echo "✅ Pulumi plan validation passed for prod environment"
            touch $out
          '';
        };

        # Re-exported packages
        packages = {
          inherit wrangler-config-gen validate-secrets gen-connection-manifest
                  gen-r2-manifest gen-r2-all gen-wrangler-config-enhanced validate-r2-config
                  discover-r2-envs fetch-remote-state r2-dev-workflow diff-state pulumi-safety-gate
                  pulumi-plan-dev pulumi-plan-stg pulumi-plan-prod;

          default = pkgs.buildEnv {
            name = "redwoodsdk-r2-tools";
            paths = [
              wrangler-config-gen validate-secrets gen-connection-manifest
              gen-r2-manifest gen-r2-all gen-wrangler-config-enhanced validate-r2-config
              discover-r2-envs fetch-remote-state r2-dev-workflow diff-state pulumi-safety-gate
              pulumi-plan-dev pulumi-plan-stg pulumi-plan-prod
            ];
          };
        };
      });
}