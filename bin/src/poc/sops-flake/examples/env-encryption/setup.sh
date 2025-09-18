#!/bin/bash
# Quick setup script for env.sh encryption
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== env.sh 暗号化セットアップ ===${NC}"

# Step 1: Check if age is installed
if ! command -v age &> /dev/null; then
    echo -e "${YELLOW}Installing age...${NC}"
    if command -v nix &> /dev/null; then
        # Try different nix installation methods
        if nix-env -iA nixos.age 2>/dev/null; then
            echo -e "${GREEN}✓ Installed age via nixos${NC}"
        elif nix profile install nixpkgs#age 2>/dev/null; then
            echo -e "${GREEN}✓ Installed age via nix profile${NC}"
        else
            echo -e "${YELLOW}Trying nix shell...${NC}"
            echo -e "${YELLOW}Run: nix shell nixpkgs#age${NC}"
            echo -e "${RED}Or install manually: https://github.com/FiloSottile/age${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Please install age first:${NC}"
        echo "  macOS: brew install age"
        echo "  Linux: apt/yum install age"
        echo "  Manual: https://github.com/FiloSottile/age"
        exit 1
    fi
fi

# Step 2: Generate age key if not exists
KEY_FILE="$HOME/.config/sops/age/keys.txt"
if [[ ! -f "$KEY_FILE" ]]; then
    echo -e "${GREEN}Generating age key...${NC}"
    mkdir -p -m 700 "$(dirname "$KEY_FILE")"
    age-keygen -o "$KEY_FILE"
    echo -e "${GREEN}✓ Age key generated at: $KEY_FILE${NC}"
else
    echo -e "${YELLOW}✓ Using existing age key${NC}"
fi

# Step 3: Get public key
PUBLIC_KEY=$(age-keygen -y "$KEY_FILE")
echo -e "${GREEN}Your public key:${NC} $PUBLIC_KEY"
echo ""

# Step 4: Create .sops.yaml if not exists
if [[ ! -f .sops.yaml ]]; then
    echo -e "${GREEN}Creating .sops.yaml...${NC}"
    cat > .sops.yaml <<EOF
# SOPS encryption rules for env files
creation_rules:
  - path_regex: .*env\.sh$
    key_groups:
      - age:
          - $PUBLIC_KEY
EOF
    echo -e "${GREEN}✓ Created .sops.yaml${NC}"
else
    echo -e "${YELLOW}✓ .sops.yaml already exists${NC}"
fi

# Step 5: Create helper scripts
echo -e "${GREEN}Creating helper scripts...${NC}"

# source-env.sh
cat > source-env.sh <<'EOF'
#!/bin/bash
# Helper script to decrypt and source env.sh securely
set -euo pipefail

# Create secure temp file with restricted permissions
TEMP_ENV=$(mktemp -t env.XXXXXX)
chmod 600 "$TEMP_ENV"

# Cleanup function
cleanup() {
    if [[ -f "$TEMP_ENV" ]]; then
        shred -u "$TEMP_ENV" 2>/dev/null || rm -f "$TEMP_ENV"
    fi
}
trap cleanup EXIT

if [[ -f env.sh.enc ]]; then
    # Decrypt to temp file and source it (no eval!)
    if sops -d env.sh.enc > "$TEMP_ENV" 2>/dev/null; then
        source "$TEMP_ENV"
        echo "✓ Environment variables loaded from env.sh.enc" >&2
    else
        echo "❌ Error: Failed to decrypt env.sh.enc" >&2
        echo "   Check: SOPS_AGE_KEY_FILE=${SOPS_AGE_KEY_FILE:-~/.config/sops/age/keys.txt}" >&2
        exit 1
    fi
elif [[ -f env.sh ]]; then
    # Fallback to plain env.sh with warning
    echo "⚠️  Warning: Using unencrypted env.sh (please encrypt it)" >&2
    source env.sh
else
    echo "❌ Error: Neither env.sh.enc nor env.sh found" >&2
    exit 1
fi
EOF
chmod +x source-env.sh

# encrypt-env.sh
cat > encrypt-env.sh <<'EOF'
#!/bin/bash
# Helper script to encrypt env.sh securely
set -euo pipefail

if [[ ! -f env.sh ]]; then
    echo "❌ Error: env.sh not found"
    echo "Create it from env.sh.example:"
    echo "  cp env.sh.example env.sh"
    echo "  vim env.sh"
    exit 1
fi

# Check for .sops.yaml
if [[ ! -f .sops.yaml ]]; then
    echo "❌ Error: .sops.yaml not found"
    echo "Run ./setup.sh first"
    exit 1
fi

# Check for age key
KEY_FILE="${SOPS_AGE_KEY_FILE:-$HOME/.config/sops/age/keys.txt}"
if [[ ! -f "$KEY_FILE" ]]; then
    echo "❌ Error: Age key not found at $KEY_FILE"
    echo "Generate one with: age-keygen -o $KEY_FILE"
    exit 1
fi

echo "🔐 Encrypting env.sh..."

# Encrypt with SOPS
if sops -e env.sh > env.sh.enc; then
    echo "✅ Created env.sh.enc"
    
    # Verify decryption works
    echo "🔍 Verifying encryption..."
    TEMP_TEST=$(mktemp)
    chmod 600 "$TEMP_TEST"
    if sops -d env.sh.enc > "$TEMP_TEST" 2>/dev/null; then
        if diff -q env.sh "$TEMP_TEST" > /dev/null; then
            echo "✅ Encryption verified successfully"
            shred -u "$TEMP_TEST" 2>/dev/null || rm -f "$TEMP_TEST"
        else
            echo "❌ Error: Decrypted content doesn't match original"
            shred -u "$TEMP_TEST" 2>/dev/null || rm -f "$TEMP_TEST"
            rm -f env.sh.enc
            exit 1
        fi
    else
        echo "❌ Error: Failed to decrypt for verification"
        shred -u "$TEMP_TEST" 2>/dev/null || rm -f "$TEMP_TEST"
        rm -f env.sh.enc
        exit 1
    fi
    
    echo ""
    echo "Next steps:"
    echo "1. IMPORTANT: Delete the plain file"
    echo "   shred -u env.sh || rm -f env.sh"
    echo ""
    echo "2. Commit the encrypted file:"
    echo "   git add env.sh.enc"
    echo "   git commit -m 'chore: add encrypted environment variables'"
    echo ""
    echo "3. To use the variables:"
    echo "   source ./source-env.sh"
else
    echo "❌ Error: Encryption failed"
    exit 1
fi
EOF
chmod +x encrypt-env.sh

# Step 6: Create example env.sh
if [[ ! -f env.sh.example ]]; then
    cat > env.sh.example <<'EOF'
#!/bin/bash
# Example environment variables file
# Copy to env.sh and fill with actual values

export API_KEY=your_api_key_here
export ORG_ID=your_org_id_here
export SECRET_TOKEN=your_secret_token_here
EOF
    echo -e "${GREEN}✓ Created env.sh.example${NC}"
fi

echo ""
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo ""
echo "Quick start:"
echo "1. Copy env.sh.example to env.sh and add your secrets"
echo "2. Run: ./encrypt-env.sh"
echo "3. Delete env.sh"
echo "4. Use: source ./source-env.sh"
echo ""
echo "To add team members:"
echo "1. Ask them to run: age-keygen -o ~/.config/sops/age/keys.txt"
echo "2. Get their public key: age-keygen -y ~/.config/sops/age/keys.txt"
echo "3. Add to .sops.yaml"
echo "4. Re-encrypt: sops updatekeys env.sh.enc"