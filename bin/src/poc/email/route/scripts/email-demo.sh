#!/usr/bin/env bash
set -e

# Email Archive Demo Script
# Demonstrates the complete email archiving flow with mock

echo "🚀 Email Archive Demo - Local Mock Testing"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if MinIO is running
check_minio() {
    echo -e "${BLUE}📡 Checking MinIO status...${NC}"
    if curl -s http://localhost:9000/minio/health/live > /dev/null; then
        echo -e "${GREEN}✅ MinIO is running${NC}"
    else
        echo -e "${YELLOW}⚠️  MinIO is not running. Starting it now...${NC}"
        ./setup-minio.sh --keep-running &
        MINIO_PID=$!
        sleep 5
    fi
}

# Start Wrangler dev server
start_worker() {
    echo -e "\n${BLUE}🔧 Starting Worker development server...${NC}"
    npm run dev:email > /tmp/wrangler.log 2>&1 &
    WRANGLER_PID=$!
    
    # Wait for server to start
    echo -n "Waiting for Worker to start"
    for i in {1..30}; do
        if curl -s http://localhost:8787/__health > /dev/null 2>&1; then
            echo -e "\n${GREEN}✅ Worker is ready${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done
}

# Send test emails
send_test_emails() {
    echo -e "\n${BLUE}📧 Sending test emails...${NC}"
    
    # Simple text email
    echo -e "\n1️⃣  Sending simple text email:"
    curl -X POST http://localhost:8787/__email \
        -H "Content-Type: application/json" \
        -d '{
            "from": "alice@example.com",
            "to": "archive@test.com",
            "subject": "Hello from Demo",
            "body": "This is a simple test email from the demo script."
        }' 2>/dev/null | jq .
    
    sleep 1
    
    # HTML email with attachment info
    echo -e "\n2️⃣  Sending HTML email with attachment metadata:"
    curl -X POST http://localhost:8787/__email \
        -H "Content-Type: application/json" \
        -d '{
            "from": "bob@company.com",
            "to": "archive@test.com",
            "subject": "Monthly Report",
            "headers": {
                "Content-Type": "multipart/mixed",
                "X-Has-Attachments": "true"
            },
            "body": "<html><body><h1>Monthly Report</h1><p>Please find the report attached.</p></body></html>"
        }' 2>/dev/null | jq .
    
    sleep 1
    
    # Multiple recipients
    echo -e "\n3️⃣  Sending email to multiple recipients:"
    curl -X POST http://localhost:8787/__email \
        -H "Content-Type: application/json" \
        -d '{
            "from": "newsletter@service.com",
            "to": "archive@test.com",
            "cc": ["user1@test.com", "user2@test.com"],
            "subject": "Newsletter Issue #42",
            "body": "Welcome to our newsletter! This month we cover..."
        }' 2>/dev/null | jq .
    
    sleep 1
}

# Show archived emails
show_archived_emails() {
    echo -e "\n${BLUE}📦 Checking archived emails in MinIO...${NC}"
    
    # Configure MinIO client
    mc alias set local http://localhost:9000 minioadmin minioadmin 2>/dev/null || true
    
    # List all archived emails
    echo -e "\n${GREEN}📋 Archived emails:${NC}"
    mc ls --recursive local/email-archive/emails/ 2>/dev/null || echo "No emails found"
    
    # Show sample content
    echo -e "\n${GREEN}📄 Sample email content:${NC}"
    LATEST_JSON=$(mc ls --recursive local/email-archive/emails/ 2>/dev/null | grep ".json" | tail -1 | awk '{print $NF}')
    if [ ! -z "$LATEST_JSON" ]; then
        echo "Latest metadata file: $LATEST_JSON"
        mc cat "local/email-archive/emails/$LATEST_JSON" 2>/dev/null | jq . || echo "Could not read metadata"
    fi
}

# Performance test
performance_test() {
    echo -e "\n${BLUE}⚡ Performance test - sending 10 emails...${NC}"
    
    START_TIME=$(date +%s)
    
    for i in {1..10}; do
        curl -s -X POST http://localhost:8787/__email \
            -H "Content-Type: application/json" \
            -d "{
                \"from\": \"perf-test-$i@example.com\",
                \"to\": \"archive@test.com\",
                \"subject\": \"Performance Test Email $i\",
                \"body\": \"This is performance test email number $i sent at $(date)\"
            }" > /dev/null
    done
    
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    echo -e "${GREEN}✅ Sent 10 emails in ${DURATION} seconds${NC}"
    echo "Average: $(echo "scale=2; $DURATION / 10" | bc) seconds per email"
}

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up...${NC}"
    [ ! -z "$WRANGLER_PID" ] && kill $WRANGLER_PID 2>/dev/null || true
    [ ! -z "$MINIO_PID" ] && kill $MINIO_PID 2>/dev/null || true
}

# Main demo flow
main() {
    trap cleanup EXIT
    
    echo "This demo will:"
    echo "1. Start MinIO (if needed)"
    echo "2. Start the Worker dev server"
    echo "3. Send various test emails"
    echo "4. Show archived emails in MinIO"
    echo "5. Run a performance test"
    echo ""
    
    read -p "Press Enter to start the demo..."
    
    check_minio
    start_worker
    send_test_emails
    show_archived_emails
    performance_test
    
    echo -e "\n${GREEN}🎉 Demo complete!${NC}"
    echo ""
    echo "You can:"
    echo "• Send more test emails: curl -X POST http://localhost:8787/__email -d '{...}'"
    echo "• View MinIO console: http://localhost:9001 (minioadmin/minioadmin)"
    echo "• Check Worker logs: tail -f /tmp/wrangler.log"
    echo ""
    read -p "Press Enter to stop the demo and cleanup..."
}

# Run the demo
main