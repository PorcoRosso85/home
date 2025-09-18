#!/usr/bin/env bash
#
# Health Check Script for Email Archive POC
# Verifies MinIO server status, bucket accessibility, and system readiness
#

set -euo pipefail

# Configuration (can be overridden by environment variables)
MINIO_ENDPOINT="${MINIO_ENDPOINT:-http://localhost:9000}"
MINIO_CONSOLE_URL="${MINIO_CONSOLE_URL:-http://localhost:9001}"
BUCKET_NAME="${BUCKET_NAME:-email-archive}"
ACCESS_KEY="${MINIO_ACCESS_KEY:-minioadmin}"
SECRET_KEY="${MINIO_SECRET_KEY:-minioadmin}"
TIMEOUT="${HEALTH_CHECK_TIMEOUT:-5}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Status tracking
CHECKS_PASSED=0
CHECKS_TOTAL=0

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((CHECKS_PASSED++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

check_total() {
    ((CHECKS_TOTAL++))
}

# Check if MinIO server is running
check_minio_server() {
    log_info "Checking MinIO server status..."
    check_total
    
    if curl -s --max-time "$TIMEOUT" "$MINIO_ENDPOINT/minio/health/live" > /dev/null 2>&1; then
        log_success "MinIO server is running and responding"
    else
        log_error "MinIO server is not responding at $MINIO_ENDPOINT"
        return 1
    fi
}

# Check MinIO readiness
check_minio_ready() {
    log_info "Checking MinIO readiness..."
    check_total
    
    if curl -s --max-time "$TIMEOUT" "$MINIO_ENDPOINT/minio/health/ready" > /dev/null 2>&1; then
        log_success "MinIO server is ready to accept requests"
    else
        log_error "MinIO server is not ready"
        return 1
    fi
}

# Check console accessibility
check_console() {
    log_info "Checking MinIO console accessibility..."
    check_total
    
    if curl -s --max-time "$TIMEOUT" -I "$MINIO_CONSOLE_URL" | grep -q "200 OK"; then
        log_success "MinIO console is accessible"
    else
        log_warning "MinIO console may not be accessible at $MINIO_CONSOLE_URL"
    fi
}

# Check MinIO client configuration
check_client_config() {
    log_info "Checking MinIO client configuration..."
    check_total
    
    if command -v mc > /dev/null 2>&1; then
        # Configure client silently
        if mc alias set health-check "$MINIO_ENDPOINT" "$ACCESS_KEY" "$SECRET_KEY" > /dev/null 2>&1; then
            log_success "MinIO client can authenticate with server"
            mc alias remove health-check > /dev/null 2>&1 || true
        else
            log_error "MinIO client authentication failed"
            return 1
        fi
    else
        log_warning "MinIO client (mc) not available for testing"
    fi
}

# Check bucket existence and accessibility
check_bucket() {
    log_info "Checking bucket '$BUCKET_NAME' status..."
    check_total
    
    if command -v mc > /dev/null 2>&1; then
        # Re-configure client for bucket check
        mc alias set health-check "$MINIO_ENDPOINT" "$ACCESS_KEY" "$SECRET_KEY" > /dev/null 2>&1
        
        if mc ls health-check/"$BUCKET_NAME" > /dev/null 2>&1; then
            log_success "Bucket '$BUCKET_NAME' is accessible"
        else
            log_error "Bucket '$BUCKET_NAME' is not accessible or doesn't exist"
            mc alias remove health-check > /dev/null 2>&1 || true
            return 1
        fi
        
        mc alias remove health-check > /dev/null 2>&1 || true
    else
        log_warning "Cannot check bucket without MinIO client"
    fi
}

# Check bucket permissions
check_bucket_permissions() {
    log_info "Checking bucket write permissions..."
    check_total
    
    if command -v mc > /dev/null 2>&1; then
        mc alias set health-check "$MINIO_ENDPOINT" "$ACCESS_KEY" "$SECRET_KEY" > /dev/null 2>&1
        
        # Create a test file
        TEST_KEY="health-check/test-$(date +%s).txt"
        TEST_CONTENT="Health check test - $(date)"
        
        if echo "$TEST_CONTENT" | mc pipe health-check/"$BUCKET_NAME"/"$TEST_KEY" > /dev/null 2>&1; then
            log_success "Bucket has write permissions"
            
            # Clean up test file
            mc rm health-check/"$BUCKET_NAME"/"$TEST_KEY" > /dev/null 2>&1 || true
        else
            log_error "Bucket write permissions failed"
            mc alias remove health-check > /dev/null 2>&1 || true
            return 1
        fi
        
        mc alias remove health-check > /dev/null 2>&1 || true
    else
        log_warning "Cannot check permissions without MinIO client"
    fi
}

# Check system resources
check_system_resources() {
    log_info "Checking system resources..."
    check_total
    
    # Check disk space (where MinIO data is stored)
    if [ -d "./minio-data" ]; then
        DISK_USAGE=$(df -h ./minio-data | tail -1 | awk '{print $5}' | sed 's/%//')
        if [ "$DISK_USAGE" -lt 90 ]; then
            log_success "Disk space is sufficient (${DISK_USAGE}% used)"
        else
            log_warning "Disk space is getting low (${DISK_USAGE}% used)"
        fi
    else
        log_warning "MinIO data directory not found, cannot check disk space"
    fi
}

# Check dependencies
check_dependencies() {
    log_info "Checking required dependencies..."
    check_total
    
    local missing_deps=()
    
    if ! command -v curl > /dev/null 2>&1; then
        missing_deps+=("curl")
    fi
    
    if ! command -v mc > /dev/null 2>&1; then
        missing_deps+=("minio-client (mc)")
    fi
    
    if [ ${#missing_deps[@]} -eq 0 ]; then
        log_success "All required dependencies are available"
    else
        log_warning "Missing dependencies: ${missing_deps[*]}"
    fi
}

# Performance test
performance_test() {
    log_info "Running basic performance test..."
    check_total
    
    if command -v mc > /dev/null 2>&1; then
        mc alias set health-check "$MINIO_ENDPOINT" "$ACCESS_KEY" "$SECRET_KEY" > /dev/null 2>&1
        
        # Create a 1KB test file
        TEST_FILE=$(mktemp)
        head -c 1024 </dev/urandom > "$TEST_FILE"
        
        START_TIME=$(date +%s.%N)
        
        if mc cp "$TEST_FILE" health-check/"$BUCKET_NAME"/performance-test.dat > /dev/null 2>&1; then
            END_TIME=$(date +%s.%N)
            DURATION=$(echo "$END_TIME - $START_TIME" | bc 2>/dev/null || echo "unknown")
            
            log_success "Performance test passed (${DURATION}s for 1KB upload)"
            
            # Clean up
            mc rm health-check/"$BUCKET_NAME"/performance-test.dat > /dev/null 2>&1 || true
        else
            log_warning "Performance test failed"
        fi
        
        rm -f "$TEST_FILE"
        mc alias remove health-check > /dev/null 2>&1 || true
    else
        log_warning "Cannot run performance test without MinIO client"
    fi
}

# Show system information
show_system_info() {
    echo
    echo "=== System Information ==="
    echo "MinIO Endpoint:    $MINIO_ENDPOINT"
    echo "MinIO Console:     $MINIO_CONSOLE_URL"
    echo "Bucket Name:       $BUCKET_NAME"
    echo "Timeout:           ${TIMEOUT}s"
    
    if command -v mc > /dev/null 2>&1; then
        echo
        echo "=== MinIO Client Version ==="
        mc --version 2>/dev/null || echo "Version information not available"
    fi
    
    echo
}

# Show final results
show_results() {
    echo
    echo "=== Health Check Results ==="
    echo "Checks passed: $CHECKS_PASSED/$CHECKS_TOTAL"
    
    if [ "$CHECKS_PASSED" -eq "$CHECKS_TOTAL" ]; then
        log_success "All health checks passed! System is ready for email archiving."
        return 0
    elif [ "$CHECKS_PASSED" -gt $((CHECKS_TOTAL / 2)) ]; then
        log_warning "Most checks passed, but some issues detected."
        return 1
    else
        log_error "Multiple health checks failed. System may not be ready."
        return 2
    fi
}

# Main health check function
main() {
    echo "Email Archive POC - Health Check"
    echo "================================"
    
    show_system_info
    
    # Run all checks
    check_dependencies
    check_minio_server
    check_minio_ready
    check_console
    check_client_config
    check_bucket
    check_bucket_permissions
    check_system_resources
    
    # Optional performance test
    if [ "${1:-}" = "--performance" ] || [ "${1:-}" = "-p" ]; then
        performance_test
    fi
    
    show_results
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [--performance] [--help]"
        echo ""
        echo "Options:"
        echo "  --performance, -p    Include performance testing"
        echo "  --help, -h          Show this help message"
        echo ""
        echo "Environment Variables:"
        echo "  MINIO_ENDPOINT      MinIO server endpoint (default: http://localhost:9000)"
        echo "  MINIO_CONSOLE_URL   MinIO console URL (default: http://localhost:9001)"
        echo "  BUCKET_NAME         S3 bucket name (default: email-archive)"
        echo "  MINIO_ACCESS_KEY    MinIO access key (default: minioadmin)"
        echo "  MINIO_SECRET_KEY    MinIO secret key (default: minioadmin)"
        echo "  HEALTH_CHECK_TIMEOUT Timeout in seconds (default: 5)"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac