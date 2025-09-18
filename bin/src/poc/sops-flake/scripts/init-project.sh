#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PROJECT_NAME=""
PROJECT_TYPE="systemd"  # Default to systemd for backward compatibility
SERVICE_NAME=""
SERVICE_USER=""
DESCRIPTION="Sops-enabled NixOS application"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --type=*)
            PROJECT_TYPE="${1#*=}"
            shift
            ;;
        --type)
            PROJECT_TYPE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [PROJECT_NAME] [--type=TYPE]"
            echo ""
            echo "Options:"
            echo "  --type=TYPE    Template type (systemd|app)"
            echo "                 systemd: For long-running services, daemons, system integration"
            echo "                 app:     For CLI tools, one-off scripts, portable applications"
            echo "  --help, -h     Show this help message"
            echo ""
            echo "If PROJECT_NAME is omitted, interactive mode will be used."
            exit 0
            ;;
        *)
            if [[ -z "$PROJECT_NAME" ]]; then
                PROJECT_NAME="$1"
            else
                echo -e "${RED}Error: Unknown argument '$1'${NC}"
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate project type
if [[ "$PROJECT_TYPE" != "systemd" && "$PROJECT_TYPE" != "app" ]]; then
    echo -e "${RED}Error: Project type must be 'systemd' or 'app'${NC}"
    exit 1
fi

# Interactive mode if no arguments
if [[ -z "$PROJECT_NAME" ]]; then
    echo -e "${GREEN}🚀 Sops-Flake Project Initialization${NC}"
    echo ""
    read -p "Project name: " PROJECT_NAME
    
    # Interactive template selection
    echo -e "\n${BLUE}Template types:${NC}"
    echo "  1. systemd - For long-running services, daemons, system integration"
    echo "  2. app     - For CLI tools, one-off scripts, portable applications"
    echo ""
    read -p "Select template type (1-2) [1]: " TYPE_CHOICE
    case "${TYPE_CHOICE:-1}" in
        1) PROJECT_TYPE="systemd" ;;
        2) PROJECT_TYPE="app" ;;
        *) 
            echo -e "${RED}Invalid choice, using systemd${NC}"
            PROJECT_TYPE="systemd"
            ;;
    esac
    
    # Only ask for service details if systemd template
    if [[ "$PROJECT_TYPE" == "systemd" ]]; then
        read -p "Service name [$PROJECT_NAME]: " SERVICE_NAME
        SERVICE_NAME="${SERVICE_NAME:-$PROJECT_NAME}"
        read -p "Service user [$SERVICE_NAME]: " SERVICE_USER
        SERVICE_USER="${SERVICE_USER:-$SERVICE_NAME}"
    fi
    
    read -p "Description [$DESCRIPTION]: " DESC_INPUT
    DESCRIPTION="${DESC_INPUT:-$DESCRIPTION}"
else
    # Non-interactive mode defaults
    if [[ "$PROJECT_TYPE" == "systemd" ]]; then
        SERVICE_NAME="${SERVICE_NAME:-$PROJECT_NAME}"
        SERVICE_USER="${SERVICE_USER:-$SERVICE_NAME}"
    fi
fi

# Validate project name
if [[ ! "$PROJECT_NAME" =~ ^[a-z][a-z0-9-]*$ ]]; then
    echo -e "${RED}Error: Project name must start with lowercase letter and contain only lowercase letters, numbers, and hyphens${NC}"
    exit 1
fi

echo -e "${YELLOW}Creating project: $PROJECT_NAME (type: $PROJECT_TYPE)${NC}"

# Create project directory
TARGET_DIR="../$PROJECT_NAME"
if [[ -d "$TARGET_DIR" ]]; then
    echo -e "${RED}Error: Directory $TARGET_DIR already exists${NC}"
    exit 1
fi

mkdir -p "$TARGET_DIR"

# Copy template files from selected template directory
TEMPLATE_DIR="templates/$PROJECT_TYPE"
if [[ ! -d "$TEMPLATE_DIR" ]]; then
    echo -e "${RED}Error: Template directory $TEMPLATE_DIR does not exist${NC}"
    exit 1
fi

cp -r "$TEMPLATE_DIR"/* "$TARGET_DIR/"
cp -r scripts "$TARGET_DIR/"
cp -r tests "$TARGET_DIR/"
cp .sops.yaml "$TARGET_DIR/"

# Replace template variables
find "$TARGET_DIR" -name "*.tmpl" | while read -r tmpl_file; do
    output_file="${tmpl_file%.tmpl}"
    sed -e "s/{{PROJECT_NAME}}/$PROJECT_NAME/g" \
        -e "s/{{SERVICE_NAME}}/$SERVICE_NAME/g" \
        -e "s/{{SERVICE_USER}}/$SERVICE_USER/g" \
        -e "s/{{DESCRIPTION}}/$DESCRIPTION/g" \
        "$tmpl_file" > "$output_file"
    rm "$tmpl_file"
done

# Create initial secrets file
mkdir -p "$TARGET_DIR/secrets"
cat > "$TARGET_DIR/secrets/app.yaml" << SECRETS
# Generated secrets for $PROJECT_NAME
api_key: "change-me-$(openssl rand -hex 16)"
db_password: "change-me-$(openssl rand -hex 16)"
SECRETS

# Update .sops.yaml with current SSH host key
SSH_KEY=$(cat /etc/ssh/ssh_host_ed25519_key.pub 2>/dev/null | cut -d' ' -f1-2 || echo "ssh-ed25519 PLACEHOLDER")
cat > "$TARGET_DIR/.sops.yaml" << SOPS
creation_rules:
  - path_regex: secrets/.*\\.(yaml|json)$
    key_groups:
      - age:
          - $SSH_KEY
SOPS

# Create .gitignore
cat > "$TARGET_DIR/.gitignore" << GITIGNORE
result
result-*
*.bak
secrets/*.bak
secrets/*.dec
*.log
GITIGNORE

echo -e "${GREEN}✅ Project initialized successfully!${NC}"
echo ""
echo "Next steps:"
echo "  1. cd $TARGET_DIR"
echo "  2. Edit secrets/app.yaml with your actual secrets"
echo "  3. Run: nix run .#encrypt-secrets"
echo "  4. Test: nix flake check"
echo "  5. Deploy: Add to your NixOS configuration"
echo ""
echo "To add more secrets:"
echo "  ./scripts/add-secret.sh <key> <value>"
