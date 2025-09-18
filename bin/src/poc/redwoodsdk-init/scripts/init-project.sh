#!/bin/bash

# Production-ready project initialization script
set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default values
DEFAULT_PROJECT_NAME="my-app"
DEFAULT_STAGE="dev"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Function to print colored output
print_color() {
    local color=$1
    shift
    echo -e "${color}$*${NC}"
}

# Function to check required tools
check_requirements() {
    local missing_tools=()
    
    for tool in node npm wrangler prisma; do
        if ! command -v $tool &> /dev/null; then
            missing_tools+=($tool)
        fi
    done
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        print_color $RED "❌ Missing required tools: ${missing_tools[*]}"
        print_color $YELLOW "Please install missing tools and try again."
        exit 1
    fi
}

# Parse arguments
PROJECT_NAME="${1:-$DEFAULT_PROJECT_NAME}"
STAGE="${2:-$DEFAULT_STAGE}"
DATABASE_ID="${3:-}"
SKIP_DEPS="${4:-false}"

# Full project name with stage
FULL_PROJECT_NAME="${PROJECT_NAME}-${STAGE}"

# Print banner
print_color $BLUE "╔════════════════════════════════════════════╗"
print_color $BLUE "║   RedwoodSDK Project Initialization        ║"
print_color $BLUE "╚════════════════════════════════════════════╝"
echo ""

print_color $GREEN "📋 Configuration:"
print_color $NC "   Project: $YELLOW$FULL_PROJECT_NAME$NC"
print_color $NC "   Stage: $YELLOW$STAGE$NC"
print_color $NC "   Directory: $YELLOW$PROJECT_ROOT$NC"
echo ""

# Check requirements
print_color $YELLOW "🔍 Checking requirements..."
check_requirements
print_color $GREEN "✅ All requirements met"
echo ""

# Step 1: Template Processing
print_color $YELLOW "📝 Processing templates..."

# Create templates directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/templates"

# Create wrangler.jsonc from template
if [ -f "$PROJECT_ROOT/wrangler.jsonc.template" ]; then
    sed -e "s/{{PROJECT_NAME}}/${FULL_PROJECT_NAME}/g" \
        -e "s/{{DATABASE_ID}}/${DATABASE_ID:-REPLACE_WITH_DATABASE_ID}/g" \
        "$PROJECT_ROOT/wrangler.jsonc.template" > "$PROJECT_ROOT/wrangler.jsonc"
    print_color $GREEN "✅ Generated wrangler.jsonc"
else
    print_color $YELLOW "⚠️  No wrangler.jsonc.template found, using existing wrangler.jsonc"
fi

# Step 2: Environment Configuration
print_color $YELLOW "🔧 Setting up environment..."

# Create .env.local if template exists
if [ -f "$PROJECT_ROOT/templates/.env.template" ]; then
    cp "$PROJECT_ROOT/templates/.env.template" "$PROJECT_ROOT/.env.local"
    sed -i "s/{{PROJECT_NAME}}/${FULL_PROJECT_NAME}/g" "$PROJECT_ROOT/.env.local"
    sed -i "s/{{STAGE}}/${STAGE}/g" "$PROJECT_ROOT/.env.local"
    print_color $GREEN "✅ Created .env.local"
fi

# Step 3: Database Setup
if [ -z "$DATABASE_ID" ]; then
    print_color $YELLOW "📦 Creating D1 database..."
    
    # Check if database already exists
    if npx wrangler d1 list 2>/dev/null | grep -q "${FULL_PROJECT_NAME}-db"; then
        print_color $YELLOW "⚠️  Database ${FULL_PROJECT_NAME}-db already exists"
        DATABASE_ID=$(npx wrangler d1 list --json 2>/dev/null | jq -r ".[] | select(.name==\"${FULL_PROJECT_NAME}-db\") | .uuid")
    else
        # Create new database
        DB_OUTPUT=$(npx wrangler d1 create "${FULL_PROJECT_NAME}-db" 2>&1)
        
        if [ $? -eq 0 ]; then
            DATABASE_ID=$(echo "$DB_OUTPUT" | grep -oP '(?<=database_id = ")[^"]+' | head -1)
            
            if [ -z "$DATABASE_ID" ]; then
                DATABASE_ID=$(echo "$DB_OUTPUT" | grep -oP '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -1)
            fi
            
            if [ -n "$DATABASE_ID" ]; then
                print_color $GREEN "✅ Database created: $DATABASE_ID"
                
                # Update wrangler.jsonc with actual database ID
                sed -i "s/REPLACE_WITH_DATABASE_ID/${DATABASE_ID}/g" "$PROJECT_ROOT/wrangler.jsonc"
            else
                print_color $RED "❌ Failed to extract database ID"
                exit 1
            fi
        else
            print_color $RED "❌ Failed to create database"
            echo "$DB_OUTPUT"
            exit 1
        fi
    fi
else
    print_color $GREEN "✅ Using existing database: $DATABASE_ID"
fi

# Step 4: Dependencies Installation
if [ "$SKIP_DEPS" != "true" ]; then
    print_color $YELLOW "📦 Installing dependencies..."
    
    cd "$PROJECT_ROOT"
    
    # Detect package manager
    if [ -f "pnpm-lock.yaml" ]; then
        pnpm install
    elif [ -f "yarn.lock" ]; then
        yarn install
    else
        npm install
    fi
    
    print_color $GREEN "✅ Dependencies installed"
else
    print_color $YELLOW "⏭️  Skipping dependency installation"
fi

# Step 5: Prisma Setup
print_color $YELLOW "🗄️  Setting up database schema..."

cd "$PROJECT_ROOT"
npx prisma generate

if [ $? -eq 0 ]; then
    print_color $GREEN "✅ Prisma client generated"
else
    print_color $RED "❌ Failed to generate Prisma client"
    exit 1
fi

# Step 6: Apply Migrations
print_color $YELLOW "📊 Applying database migrations..."

npx wrangler d1 migrations apply "${FULL_PROJECT_NAME}-db" --local

if [ $? -eq 0 ]; then
    print_color $GREEN "✅ Migrations applied"
else
    print_color $YELLOW "⚠️  Failed to apply migrations (this might be normal for first run)"
fi

# Step 7: Create secrets template
print_color $YELLOW "🔐 Creating secrets template..."

cat > "$PROJECT_ROOT/templates/secrets.yml" << EOF
# Secrets configuration for ${FULL_PROJECT_NAME}
# Copy this to secrets.${STAGE}.yml and fill in actual values

# Authentication
WEBAUTHN_RP_ID: "your-domain.com"
SESSION_SECRET: "generate-random-secret-here"

# External Services (if needed)
# API_KEY: "your-api-key"
# WEBHOOK_SECRET: "your-webhook-secret"

# Database (auto-configured)
DATABASE_ID: "${DATABASE_ID}"
EOF

print_color $GREEN "✅ Created secrets template"

# Step 8: Git Setup
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    print_color $YELLOW "📚 Initializing Git repository..."
    cd "$PROJECT_ROOT"
    git init
    git add .
    git commit -m "Initial commit: ${FULL_PROJECT_NAME}"
    print_color $GREEN "✅ Git repository initialized"
fi

# Final Summary
echo ""
print_color $BLUE "╔════════════════════════════════════════════╗"
print_color $BLUE "║   🎉 Project Initialization Complete!      ║"
print_color $BLUE "╚════════════════════════════════════════════╝"
echo ""

print_color $GREEN "📋 Project Details:"
print_color $NC "   Name: $FULL_PROJECT_NAME"
print_color $NC "   Database: ${FULL_PROJECT_NAME}-db"
print_color $NC "   Database ID: $DATABASE_ID"
echo ""

print_color $GREEN "🚀 Next Steps:"
print_color $NC "   1. Review configuration in wrangler.jsonc"
print_color $NC "   2. Set up secrets: cp templates/secrets.yml secrets.${STAGE}.yml"
print_color $NC "   3. Start development: npm run dev"
print_color $NC "   4. Run tests: npm test"
print_color $NC "   5. Deploy: npm run deploy:safe"
echo ""

print_color $YELLOW "📚 Documentation:"
print_color $NC "   - Production Deploy: docs/PRODUCTION_DEPLOY.md"
print_color $NC "   - Troubleshooting: docs/TROUBLESHOOTING.md"
print_color $NC "   - Boilerplate Guide: docs/BOILERPLATE.md"
echo ""