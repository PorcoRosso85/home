#!/bin/bash

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
DEFAULT_PROJECT_NAME="my-app"
DEFAULT_STAGE="dev"

# Parse arguments
PROJECT_NAME="${1:-$DEFAULT_PROJECT_NAME}"
STAGE="${2:-$DEFAULT_STAGE}"
DATABASE_ID="${3:-}"

# Add stage suffix to project name
FULL_PROJECT_NAME="${PROJECT_NAME}-${STAGE}"

echo -e "${GREEN}🚀 Initializing RedwoodSDK project${NC}"
echo -e "   Project: ${YELLOW}${FULL_PROJECT_NAME}${NC}"
echo -e "   Stage: ${YELLOW}${STAGE}${NC}"

# Check if template exists
if [ ! -f "wrangler.jsonc.template" ]; then
    echo -e "${RED}❌ Error: wrangler.jsonc.template not found${NC}"
    exit 1
fi

# Create database if DATABASE_ID not provided
if [ -z "$DATABASE_ID" ]; then
    echo -e "${YELLOW}📦 Creating new D1 database...${NC}"
    DB_OUTPUT=$(npx wrangler d1 create "${FULL_PROJECT_NAME}-db" 2>&1)
    
    if [ $? -eq 0 ]; then
        # Extract database ID from output
        DATABASE_ID=$(echo "$DB_OUTPUT" | grep -oP '(?<=database_id = ")[^"]+' | head -1)
        
        if [ -z "$DATABASE_ID" ]; then
            # Try alternative pattern
            DATABASE_ID=$(echo "$DB_OUTPUT" | grep -oP '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -1)
        fi
        
        if [ -n "$DATABASE_ID" ]; then
            echo -e "${GREEN}✅ Database created: ${DATABASE_ID}${NC}"
        else
            echo -e "${YELLOW}⚠️  Database might be created but ID couldn't be extracted${NC}"
            echo -e "   Please check the output and add manually to wrangler.jsonc"
            echo -e "   Output: $DB_OUTPUT"
            DATABASE_ID="REPLACE_WITH_DATABASE_ID"
        fi
    else
        echo -e "${RED}❌ Failed to create database${NC}"
        echo -e "   Error: $DB_OUTPUT"
        DATABASE_ID="REPLACE_WITH_DATABASE_ID"
    fi
else
    echo -e "${GREEN}✅ Using existing database: ${DATABASE_ID}${NC}"
fi

# Create wrangler.jsonc from template
echo -e "${YELLOW}📝 Generating wrangler.jsonc...${NC}"

# Use sed to replace placeholders
sed -e "s/{{PROJECT_NAME}}/${FULL_PROJECT_NAME}/g" \
    -e "s/{{DATABASE_ID}}/${DATABASE_ID}/g" \
    wrangler.jsonc.template > wrangler.jsonc

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Created wrangler.jsonc for ${FULL_PROJECT_NAME}${NC}"
else
    echo -e "${RED}❌ Failed to create wrangler.jsonc${NC}"
    exit 1
fi

# Update flake.nix production URL if it exists
if [ -f "flake.nix" ]; then
    echo -e "${YELLOW}📝 Updating flake.nix production URL...${NC}"
    # Get the Cloudflare account subdomain from existing URL or use placeholder
    SUBDOMAIN=$(grep -oP '(?<=https://)[^.]+(?=\..*\.workers\.dev)' flake.nix | head -1 || echo "YOUR_SUBDOMAIN")
    NEW_URL="https://${FULL_PROJECT_NAME}.${SUBDOMAIN}.workers.dev"
    
    # Update the production URL in flake.nix
    sed -i "s|https://[^\"]*\.workers\.dev|${NEW_URL}|g" flake.nix
    echo -e "${GREEN}✅ Updated production URL to: ${NEW_URL}${NC}"
fi

# Show next steps
echo ""
echo -e "${GREEN}🎉 Project initialization complete!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Review the generated wrangler.jsonc"
if [ "$DATABASE_ID" = "REPLACE_WITH_DATABASE_ID" ]; then
    echo "  2. Replace DATABASE_ID in wrangler.jsonc with your actual database ID"
    echo "  3. Run: pnpm run migrate:dev    # Apply migrations locally"
else
    echo "  2. Run: pnpm run migrate:dev    # Apply migrations locally"
    echo "  3. Run: pnpm run dev            # Start development server"
fi
echo ""
echo -e "${YELLOW}To deploy:${NC}"
echo "  pnpm run release"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  - Project: ${FULL_PROJECT_NAME}"
echo "  - Database: ${FULL_PROJECT_NAME}-db"
echo "  - Database ID: ${DATABASE_ID}"