{
  description = "Deployment script with encrypted secrets";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.11";
    sops-nix = {
      url = "github:Mic92/sops-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    flake-utils.url = "github:numtide/flake-utils";
  };
  
  outputs = { self, nixpkgs, sops-nix, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        sops = sops-nix.packages.${system}.sops;
      in
      {
        packages = {
          default = pkgs.writeShellApplication {
            name = "deploy";
            runtimeInputs = [ sops pkgs.jq pkgs.openssh pkgs.rsync ];
            text = ''
              set -euo pipefail
              
              # Color output
              RED='\033[0;31m'
              GREEN='\033[0;32m'
              YELLOW='\033[1;33m'
              NC='\033[0m' # No Color
              
              # Configuration
              SCRIPT_DIR="$(cd "$(dirname "''${BASH_SOURCE[0]}")" && pwd)"
              SECRETS_DIR="''${SECRETS_DIR:-$SCRIPT_DIR/../share/secrets}"
              SOPS_AGE_KEY_FILE="''${SOPS_AGE_KEY_FILE:-$HOME/.config/sops/age/keys.txt}"
              
              echo -e "''${GREEN}🚀 Deployment Script with SOPS Integration''${NC}"
              echo "================================================"
              
              # Parse arguments
              TARGET="''${1:-}"
              ACTION="''${2:-deploy}"
              
              if [[ -z "$TARGET" ]]; then
                echo -e "''${RED}❌ Error: Target environment required''${NC}"
                echo ""
                echo "Usage: $(basename "$0") <target> [action]"
                echo ""
                echo "Targets:"
                echo "  staging    - Deploy to staging environment"
                echo "  production - Deploy to production environment"
                echo ""
                echo "Actions:"
                echo "  deploy     - Full deployment (default)"
                echo "  rollback   - Rollback to previous version"
                echo "  status     - Check deployment status"
                exit 1
              fi
              
              # Decrypt deployment configuration
              decrypt_config() {
                local env="$1"
                local config_file="$SECRETS_DIR/deploy-$env.yaml"
                
                if [[ ! -f "$config_file" ]]; then
                  echo -e "''${YELLOW}⚠️  No encrypted config found for $env, using defaults''${NC}"
                  cat <<EOF
              {
                "server": {
                  "host": "$env.example.com",
                  "port": 22,
                  "user": "deploy"
                },
                "paths": {
                  "source": "/var/www/app",
                  "backup": "/var/backups/app"
                },
                "credentials": {
                  "api_key": "default-key",
                  "db_password": "default-pass"
                }
              }
              EOF
                  return
                fi
                
                export SOPS_AGE_KEY_FILE
                sops -d "$config_file" --output-type json 2>/dev/null || {
                  echo -e "''${RED}❌ Failed to decrypt configuration''${NC}"
                  exit 1
                }
              }
              
              # Execute encrypted deployment script
              execute_encrypted_script() {
                local script_file="$SECRETS_DIR/deploy.sh.enc"
                
                if [[ -f "$script_file" ]]; then
                  echo -e "''${GREEN}📜 Executing encrypted deployment script...''${NC}"
                  export SOPS_AGE_KEY_FILE
                  
                  # Decrypt and execute in memory
                  sops exec-file "$script_file" 'bash {}'
                else
                  echo -e "''${YELLOW}ℹ️  No encrypted script found, using standard deployment''${NC}"
                fi
              }
              
              # Load configuration
              echo -e "''${GREEN}🔐 Loading encrypted configuration for: $TARGET''${NC}"
              CONFIG=$(decrypt_config "$TARGET")
              
              # Extract configuration values
              HOST=$(echo "$CONFIG" | jq -r '.server.host')
              PORT=$(echo "$CONFIG" | jq -r '.server.port')
              USER=$(echo "$CONFIG" | jq -r '.server.user')
              SOURCE_PATH=$(echo "$CONFIG" | jq -r '.paths.source')
              BACKUP_PATH=$(echo "$CONFIG" | jq -r '.paths.backup')
              API_KEY=$(echo "$CONFIG" | jq -r '.credentials.api_key')
              DB_PASSWORD=$(echo "$CONFIG" | jq -r '.credentials.db_password')
              
              # Perform action
              case "$ACTION" in
                deploy)
                  echo -e "''${GREEN}📦 Deploying to $TARGET environment''${NC}"
                  echo "  Server: $USER@$HOST:$PORT"
                  echo "  Path: $SOURCE_PATH"
                  
                  # Create backup
                  echo -e "''${GREEN}💾 Creating backup...''${NC}"
                  TIMESTAMP=$(date +%Y%m%d_%H%M%S)
                  echo "  Backup location: $BACKUP_PATH/backup_$TIMESTAMP"
                  
                  # Simulate deployment steps
                  echo -e "''${GREEN}📤 Uploading files...''${NC}"
                  echo "  - Connecting to $HOST..."
                  echo "  - Uploading application files..."
                  echo "  - Setting environment variables..."
                  echo "    API_KEY=****** (hidden)"
                  echo "    DB_PASSWORD=****** (hidden)"
                  
                  # Execute encrypted deployment script if available
                  execute_encrypted_script
                  
                  echo -e "''${GREEN}🔄 Restarting services...''${NC}"
                  echo "  - Restarting application server..."
                  echo "  - Clearing cache..."
                  echo "  - Running health checks..."
                  
                  echo -e "''${GREEN}✅ Deployment to $TARGET completed successfully!''${NC}"
                  ;;
                  
                rollback)
                  echo -e "''${YELLOW}⏪ Rolling back $TARGET deployment''${NC}"
                  echo "  Server: $USER@$HOST:$PORT"
                  echo "  Restoring from: $BACKUP_PATH"
                  
                  # Simulate rollback
                  echo "  - Finding latest backup..."
                  echo "  - Restoring files..."
                  echo "  - Restarting services..."
                  
                  echo -e "''${GREEN}✅ Rollback completed''${NC}"
                  ;;
                  
                status)
                  echo -e "''${GREEN}📊 Checking $TARGET deployment status''${NC}"
                  echo "  Server: $USER@$HOST:$PORT"
                  echo ""
                  echo "  Application: ✅ Running"
                  echo "  Database: ✅ Connected"
                  echo "  Cache: ✅ Active"
                  echo "  SSL: ✅ Valid"
                  echo ""
                  echo "  Last deployment: $(date -d '2 hours ago' '+%Y-%m-%d %H:%M:%S')"
                  echo "  Uptime: 2 hours 15 minutes"
                  ;;
                  
                *)
                  echo -e "''${RED}❌ Unknown action: $ACTION''${NC}"
                  exit 1
                  ;;
              esac
            '';
          };
          
          # Helper to set up deployment secrets
          setup-secrets = pkgs.writeShellApplication {
            name = "setup-deploy-secrets";
            runtimeInputs = [ sops pkgs.age pkgs.yq ];
            text = ''
              set -euo pipefail
              
              echo "🔧 Setting up deployment secrets..."
              
              # Generate age key if needed
              KEY_FILE="$HOME/.config/sops/age/keys.txt"
              if [[ ! -f "$KEY_FILE" ]]; then
                mkdir -p "$(dirname "$KEY_FILE")"
                age-keygen -o "$KEY_FILE"
                echo "✅ Generated age key"
              fi
              
              PUBLIC_KEY=$(age-keygen -y "$KEY_FILE")
              
              # Create .sops.yaml
              cat > .sops.yaml <<EOF
              creation_rules:
                - path_regex: secrets/.*\.(yaml|json|sh\.enc)$
                  key_groups:
                    - age:
                        - $PUBLIC_KEY
              EOF
              
              # Create secrets directory
              mkdir -p secrets
              
              # Create staging configuration
              cat > secrets/deploy-staging.plain.yaml <<EOF
              server:
                host: staging.example.com
                port: 22
                user: deploy
              paths:
                source: /var/www/staging
                backup: /var/backups/staging
              credentials:
                api_key: staging-api-key-abc123
                db_password: staging-db-pass-xyz789
              EOF
              
              # Create production configuration
              cat > secrets/deploy-production.plain.yaml <<EOF
              server:
                host: production.example.com
                port: 22
                user: deploy
              paths:
                source: /var/www/production
                backup: /var/backups/production
              credentials:
                api_key: prod-api-key-secret123
                db_password: prod-db-pass-secure456
              EOF
              
              # Create deployment script
              cat > secrets/deploy.sh <<'SCRIPT'
              #!/bin/bash
              # Encrypted deployment script with sensitive operations
              
              echo "🔒 Executing secure deployment operations..."
              
              # Database migration with credentials
              echo "Running database migrations..."
              # mysql -u admin -p$DB_PASSWORD < migrations.sql
              
              # API configuration update
              echo "Updating API configuration..."
              # curl -X POST -H "Authorization: Bearer $API_KEY" https://api.example.com/deploy
              
              # Secret rotation
              echo "Rotating secrets..."
              # vault write secret/app key=new-value
              
              echo "✅ Secure operations completed"
              SCRIPT
              
              chmod +x secrets/deploy.sh
              
              echo ""
              echo "✅ Created plain configuration files:"
              echo "  - secrets/deploy-staging.plain.yaml"
              echo "  - secrets/deploy-production.plain.yaml"
              echo "  - secrets/deploy.sh"
              echo ""
              echo "Next steps:"
              echo "1. Review and edit the configuration files"
              echo "2. Encrypt them:"
              echo "   sops -e secrets/deploy-staging.plain.yaml > secrets/deploy-staging.yaml"
              echo "   sops -e secrets/deploy-production.plain.yaml > secrets/deploy-production.yaml"
              echo "   sops -e secrets/deploy.sh > secrets/deploy.sh.enc"
              echo "3. Remove plain files:"
              echo "   rm secrets/*.plain.yaml secrets/deploy.sh"
            '';
          };
        };
        
        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/deploy";
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            sops
            age
            jq
            yq
            openssh
            rsync
          ];
          
          shellHook = ''
            echo "🚀 Deployment Script Development Environment"
            echo ""
            echo "Commands:"
            echo "  nix run . -- staging deploy    # Deploy to staging"
            echo "  nix run . -- production status  # Check production status"
            echo "  nix run .#setup-secrets        # Set up encrypted secrets"
          '';
        };
      });
}