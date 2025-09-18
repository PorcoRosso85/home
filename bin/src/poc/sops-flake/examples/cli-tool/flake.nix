{
  description = "CLI tool with sops-managed configuration";
  
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
            name = "sops-cli-tool";
            runtimeInputs = [ sops pkgs.jq pkgs.yq ];
            text = ''
              set -euo pipefail
              
              # Configuration paths
              SCRIPT_DIR="$(cd "$(dirname "''${BASH_SOURCE[0]}")" && pwd)"
              SECRETS_FILE="''${SECRETS_FILE:-$SCRIPT_DIR/../share/secrets/config.yaml}"
              SOPS_AGE_KEY_FILE="''${SOPS_AGE_KEY_FILE:-$HOME/.config/sops/age/keys.txt}"
              
              # Function to decrypt config
              decrypt_config() {
                if [[ -f "$SECRETS_FILE" ]]; then
                  export SOPS_AGE_KEY_FILE
                  sops -d "$SECRETS_FILE" 2>/dev/null || echo "{}"
                else
                  echo "{}"
                fi
              }
              
              # Parse arguments
              COMMAND="''${1:-help}"
              shift || true
              
              case "$COMMAND" in
                process)
                  echo "🔧 Processing with encrypted configuration..."
                  CONFIG=$(decrypt_config)
                  
                  # Extract configuration values
                  API_ENDPOINT=$(echo "$CONFIG" | yq -r '.api.endpoint // "https://api.example.com"')
                  API_TOKEN=$(echo "$CONFIG" | yq -r '.api.token // "no-token"')
                  TIMEOUT=$(echo "$CONFIG" | yq -r '.settings.timeout // 30')
                  
                  echo "📍 API Endpoint: $API_ENDPOINT"
                  echo "⏱️  Timeout: ''${TIMEOUT}s"
                  echo "🔑 Token configured: $([ "$API_TOKEN" != "no-token" ] && echo "Yes" || echo "No")"
                  
                  # Process the provided data
                  if [[ $# -gt 0 ]]; then
                    echo "📝 Processing: $*"
                    # Simulate API call
                    echo "✅ Data processed successfully"
                  else
                    echo "⚠️  No data provided to process"
                  fi
                  ;;
                  
                config)
                  echo "📋 Current configuration:"
                  CONFIG=$(decrypt_config)
                  echo "$CONFIG" | yq -C '.'
                  ;;
                  
                encrypt-config)
                  if [[ ! -f "$SOPS_AGE_KEY_FILE" ]]; then
                    echo "❌ Age key not found at $SOPS_AGE_KEY_FILE"
                    echo "   Run: age-keygen -o $SOPS_AGE_KEY_FILE"
                    exit 1
                  fi
                  
                  PLAIN_CONFIG="''${1:-}"
                  if [[ -z "$PLAIN_CONFIG" ]] || [[ ! -f "$PLAIN_CONFIG" ]]; then
                    echo "❌ Usage: $0 encrypt-config <plain-config-file>"
                    exit 1
                  fi
                  
                  echo "🔐 Encrypting configuration..."
                  export SOPS_AGE_KEY_FILE
                  sops -e "$PLAIN_CONFIG" > "$SECRETS_FILE"
                  echo "✅ Configuration encrypted to: $SECRETS_FILE"
                  ;;
                  
                help|*)
                  cat <<EOF
              CLI Tool with SOPS-managed secrets
              
              Usage: $(basename "$0") <command> [arguments]
              
              Commands:
                process <data>     Process data using encrypted configuration
                config            Show current configuration (decrypted)
                encrypt-config    Encrypt a plain configuration file
                help              Show this help message
              
              Environment Variables:
                SECRETS_FILE        Path to encrypted config (default: ../share/secrets/config.yaml)
                SOPS_AGE_KEY_FILE   Path to age private key (default: ~/.config/sops/age/keys.txt)
              
              Examples:
                # Process some data
                $(basename "$0") process "Hello World"
                
                # View configuration
                $(basename "$0") config
                
                # Encrypt configuration
                $(basename "$0") encrypt-config plain-config.yaml
              EOF
                  ;;
              esac
            '';
          };
          
          # Helper to create initial configuration
          init-config = pkgs.writeShellApplication {
            name = "init-config";
            runtimeInputs = [ pkgs.age ];
            text = ''
              set -euo pipefail
              
              echo "🔧 Initializing CLI tool configuration..."
              
              # Generate age key if not exists
              KEY_FILE="$HOME/.config/sops/age/keys.txt"
              if [[ ! -f "$KEY_FILE" ]]; then
                mkdir -p "$(dirname "$KEY_FILE")"
                age-keygen -o "$KEY_FILE"
                echo "✅ Generated age key at: $KEY_FILE"
              else
                echo "ℹ️  Using existing age key from: $KEY_FILE"
              fi
              
              # Get public key
              PUBLIC_KEY=$(age-keygen -y "$KEY_FILE")
              
              # Create .sops.yaml
              cat > .sops.yaml <<EOF
              creation_rules:
                - path_regex: secrets/.*\.(yaml|json)$
                  key_groups:
                    - age:
                        - $PUBLIC_KEY
              EOF
              echo "✅ Created .sops.yaml with your public key"
              
              # Create sample configuration
              mkdir -p secrets
              cat > secrets/config.plain.yaml <<EOF
              api:
                endpoint: https://api.example.com
                token: your-secret-api-token
              settings:
                timeout: 30
                retries: 3
                debug: false
              features:
                cache: true
                logging: true
              EOF
              echo "✅ Created sample configuration: secrets/config.plain.yaml"
              echo ""
              echo "Next steps:"
              echo "1. Edit secrets/config.plain.yaml with your actual values"
              echo "2. Encrypt it: sops -e secrets/config.plain.yaml > secrets/config.yaml"
              echo "3. Delete the plain file: rm secrets/config.plain.yaml"
            '';
          };
        };
        
        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/sops-cli-tool";
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            sops
            age
            jq
            yq
          ];
          
          shellHook = ''
            echo "🛠️  CLI Tool Development Environment"
            echo "Commands available:"
            echo "  - sops: Encrypt/decrypt secrets"
            echo "  - age-keygen: Generate encryption keys"
            echo "  - jq/yq: Process JSON/YAML"
            echo ""
            echo "Run 'nix run .#init-config' to set up initial configuration"
          '';
        };
      });
}