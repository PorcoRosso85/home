# RunPod SSH Flake - API Integration Specification

## Overview

This document provides comprehensive specifications for integrating with the RunPod GraphQL API and GitHub APIs. It defines authentication flows, error handling patterns, rate limiting considerations, and security requirements for the RunPod SSH Flake system.

## RunPod GraphQL API Integration

### API Endpoint Information

#### Primary Endpoint
- **URL**: `https://api.runpod.io/graphql`
- **Protocol**: HTTPS only
- **Content-Type**: `application/json`
- **Authentication**: Bearer token in Authorization header

#### Alternative Endpoints (Environment-Specific)
```bash
# Production (default)
RUNPOD_API_URL="https://api.runpod.io/graphql"

# Development/Testing (if different)
RUNPOD_API_URL="https://api.runpod.io/graphql"
```

### Authentication Flow Design

#### 1. API Key Authentication
```bash
# Header format
Authorization: Bearer <RUNPOD_API_KEY>
Content-Type: application/json

# Environment variable
export RUNPOD_API_KEY="your_api_key_here"
```

#### 2. Authentication Validation
```graphql
# Test authentication with minimal query
query testAuth {
  myself {
    id
    email
  }
}
```

Expected successful response:
```json
{
  "data": {
    "myself": {
      "id": "user_id",
      "email": "user@example.com"
    }
  }
}
```

Authentication failure response:
```json
{
  "errors": [
    {
      "message": "Invalid authorization token",
      "locations": [{"line": 2, "column": 3}],
      "extensions": {
        "code": "UNAUTHENTICATED"
      }
    }
  ]
}
```

### Core GraphQL Operations

#### 1. Pod Creation (podRentInterruptable)

```graphql
mutation createPod($input: PodRentInterruptableInput!) {
  podRentInterruptable(input: $input) {
    id
    desiredStatus
    imageName
    machineId
    machine {
      podHostId
    }
  }
}
```

**Input Variables Schema:**
```json
{
  "input": {
    "gpuCount": "number (required)",
    "bidPerGpu": "number (required, in USD)",
    "gpuTypeId": "string (required)",
    "imageName": "string (required)", 
    "minVcpuCount": "number (optional, default: 1)",
    "minMemoryInGb": "number (optional, default: 4)",
    "dockerArgs": "string (optional)",
    "ports": "string (optional, e.g. '22/tcp')",
    "volumeInGb": "number (optional)",
    "containerDiskInGb": "number (optional)",
    "startSSH": "boolean (optional, default: false)"
  }
}
```

**Example Request:**
```json
{
  "input": {
    "gpuCount": 1,
    "bidPerGpu": 0.50,
    "gpuTypeId": "NVIDIA GeForce RTX 4090",
    "imageName": "runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel-ubuntu22.04",
    "minVcpuCount": 4,
    "minMemoryInGb": 16,
    "ports": "22/tcp",
    "volumeInGb": 50,
    "containerDiskInGb": 50,
    "startSSH": true
  }
}
```

**Success Response:**
```json
{
  "data": {
    "podRentInterruptable": {
      "id": "pod-12345",
      "desiredStatus": "RUNNING",
      "imageName": "runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel-ubuntu22.04",
      "machineId": "machine-67890",
      "machine": {
        "podHostId": "host-abcdef"
      }
    }
  }
}
```

#### 2. Pod Status Query

```graphql
query getPod($podId: String!) {
  pod(input: {podId: $podId}) {
    id
    desiredStatus
    lastStatusChange
    imageName
    machineId
    machine {
      podHostId
    }
    runtime {
      uptimeInSeconds
      ports {
        ip
        isIpPublic  
        privatePort
        publicPort
      }
      gpus {
        id
        gpuUtilPercent
        memoryUtilPercent
      }
    }
  }
}
```

**Variables:**
```json
{
  "podId": "pod-12345"
}
```

**Success Response:**
```json
{
  "data": {
    "pod": {
      "id": "pod-12345",
      "desiredStatus": "RUNNING", 
      "lastStatusChange": "2023-10-01T10:30:00.000Z",
      "imageName": "runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel-ubuntu22.04",
      "machineId": "machine-67890",
      "machine": {
        "podHostId": "host-abcdef"
      },
      "runtime": {
        "uptimeInSeconds": 3600,
        "ports": [
          {
            "ip": "198.51.100.1",
            "isIpPublic": true,
            "privatePort": 22,
            "publicPort": 22001
          }
        ],
        "gpus": [
          {
            "id": "gpu-1",
            "gpuUtilPercent": 0,
            "memoryUtilPercent": 5
          }
        ]
      }
    }
  }
}
```

#### 3. Pod Resumption

```graphql
mutation resumePod($input: PodResumeInput!) {
  podResume(input: $input) {
    id
    desiredStatus
    imageName
  }
}
```

**Variables:**
```json
{
  "input": {
    "podId": "pod-12345",
    "gpuCount": 1,
    "bidPerGpu": 0.50
  }
}
```

#### 4. Pod Termination

```graphql
mutation stopPod($input: PodStopInput!) {
  podStop(input: $input) {
    id
    desiredStatus
  }
}
```

**Variables:**
```json
{
  "input": {
    "podId": "pod-12345"
  }
}
```

#### 5. Pod Listing

```graphql
query listPods {
  myself {
    pods {
      id
      desiredStatus
      lastStatusChange
      imageName
      runtime {
        uptimeInSeconds
      }
    }
  }
}
```

### GPU Type Discovery

#### Available GPU Types Query
```graphql
query getGpuTypes {
  gpuTypes {
    id
    displayName
    memoryInGb
    secureCloud
    communityCloud
    lowestPrice {
      minimumBidPrice
      uninterruptablePrice
    }
  }
}
```

**Response Example:**
```json
{
  "data": {
    "gpuTypes": [
      {
        "id": "NVIDIA GeForce RTX 4090",
        "displayName": "RTX 4090",
        "memoryInGb": 24,
        "secureCloud": true,
        "communityCloud": true,
        "lowestPrice": {
          "minimumBidPrice": 0.39,
          "uninterruptablePrice": 1.89
        }
      }
    ]
  }
}
```

### Error Handling Patterns

#### 1. Network-Level Errors

**Connection Timeout:**
```json
{
  "error": "Network timeout",
  "code": "NETWORK_TIMEOUT",
  "details": {
    "timeout_seconds": 30,
    "endpoint": "https://api.runpod.io/graphql"
  }
}
```

**DNS Resolution Failure:**
```json
{
  "error": "DNS resolution failed",
  "code": "DNS_ERROR", 
  "details": {
    "hostname": "api.runpod.io"
  }
}
```

#### 2. Authentication Errors

**Invalid API Key:**
```json
{
  "errors": [
    {
      "message": "Invalid authorization token",
      "extensions": {
        "code": "UNAUTHENTICATED"
      }
    }
  ]
}
```

**Expired Token:**
```json
{
  "errors": [
    {
      "message": "Token has expired",
      "extensions": {
        "code": "UNAUTHENTICATED",
        "expiredAt": "2023-10-01T00:00:00Z"
      }
    }
  ]
}
```

#### 3. Resource Errors

**Insufficient Credits:**
```json
{
  "errors": [
    {
      "message": "Insufficient credit balance",
      "extensions": {
        "code": "INSUFFICIENT_CREDITS",
        "balance": 5.50,
        "required": 15.00
      }
    }
  ]
}
```

**GPU Unavailable:**
```json
{
  "errors": [
    {
      "message": "No GPUs available for specified configuration",
      "extensions": {
        "code": "RESOURCE_UNAVAILABLE",
        "gpuType": "NVIDIA GeForce RTX 4090",
        "requestedCount": 2
      }
    }
  ]
}
```

**Bid Price Too Low:**
```json
{
  "errors": [
    {
      "message": "Bid price below minimum required",
      "extensions": {
        "code": "BID_TOO_LOW",
        "bidPrice": 0.10,
        "minimumBid": 0.25
      }
    }
  ]
}
```

#### 4. Validation Errors

**Invalid Pod ID:**
```json
{
  "errors": [
    {
      "message": "Pod not found",
      "extensions": {
        "code": "NOT_FOUND",
        "podId": "invalid-pod-id"
      }
    }
  ]
}
```

**Invalid Input Parameters:**
```json
{
  "errors": [
    {
      "message": "Invalid input parameters",
      "extensions": {
        "code": "BAD_USER_INPUT",
        "field": "gpuCount",
        "value": -1,
        "constraint": "Must be positive integer"
      }
    }
  ]
}
```

### Rate Limiting Considerations

#### Rate Limit Information
- **Default Limit**: 100 requests per minute per API key
- **Burst Limit**: 10 requests per second
- **Rate Limit Headers**: Not consistently provided
- **429 Status Code**: Indicates rate limit exceeded

#### Rate Limiting Response
```json
{
  "errors": [
    {
      "message": "Rate limit exceeded",
      "extensions": {
        "code": "RATE_LIMITED",
        "resetAt": "2023-10-01T10:31:00Z",
        "limit": 100,
        "window": "60s"
      }
    }
  ]
}
```

#### Rate Limiting Strategy
```bash
# Exponential backoff implementation
handle_rate_limit() {
    local attempt=1
    local max_attempts=5
    local base_delay=5
    
    while [[ $attempt -le $max_attempts ]]; do
        if make_api_request; then
            return 0
        fi
        
        # Check if rate limited
        if [[ $response_code -eq 429 ]]; then
            local delay=$((base_delay * 2**(attempt-1)))
            echo "Rate limited, waiting ${delay}s before retry $attempt/$max_attempts"
            sleep $delay
        else
            return 1  # Non-rate-limit error
        fi
        
        ((attempt++))
    done
    
    return 1
}
```

### Request/Response Logging

#### Request Logging Format
```json
{
  "timestamp": "2023-10-01T10:30:00Z",
  "type": "request",
  "operation": "createPod",
  "variables": {
    "gpuCount": 1,
    "gpuTypeId": "[MASKED]"
  },
  "headers": {
    "Authorization": "Bearer [MASKED]",
    "Content-Type": "application/json"
  }
}
```

#### Response Logging Format
```json
{
  "timestamp": "2023-10-01T10:30:01Z", 
  "type": "response",
  "operation": "createPod",
  "status": "success",
  "duration_ms": 1234,
  "data": {
    "podId": "pod-12345"
  }
}
```

#### Error Logging Format
```json
{
  "timestamp": "2023-10-01T10:30:01Z",
  "type": "error", 
  "operation": "createPod",
  "status": "failed",
  "duration_ms": 5000,
  "error": {
    "code": "NETWORK_TIMEOUT",
    "message": "Request timeout after 30 seconds"
  }
}
```

## GitHub API Integration

### GitHub Actions Runner API

#### 1. Generate Runner Token
```bash
# Organization-level runner
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/orgs/$ORG/actions/runners/registration-token"

# Repository-level runner  
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runners/registration-token"
```

**Success Response:**
```json
{
  "token": "GHRT_1234567890abcdef",
  "expires_at": "2023-10-01T11:30:00Z"
}
```

#### 2. Generate Runner Removal Token
```bash
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runners/remove-token"
```

#### 3. List Repository Runners
```bash
curl -H "Authorization: token $GITHUB_TOKEN" \
     -H "Accept: application/vnd.github+json" \
     "https://api.github.com/repos/$OWNER/$REPO/actions/runners"
```

**Response:**
```json
{
  "total_count": 1,
  "runners": [
    {
      "id": 123,
      "name": "runpod-runner-1",
      "os": "linux",
      "status": "online",
      "busy": false,
      "labels": [
        {"id": 1, "name": "self-hosted", "type": "read-only"},
        {"id": 2, "name": "linux", "type": "read-only"},
        {"id": 3, "name": "x64", "type": "read-only"}
      ]
    }
  ]
}
```

### GitHub Authentication Patterns

#### Personal Access Token (PAT)
```bash
# Classic token with repo and admin:org scope
GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"

# Fine-grained token (preferred)
GITHUB_TOKEN="github_pat_xxxxxxxxxxxxxxxxxxxx"
```

#### GitHub App Authentication
```bash
# Generate JWT for GitHub App
APP_ID=12345
PRIVATE_KEY_PATH="/path/to/private-key.pem"

generate_jwt() {
    local header='{"alg":"RS256","typ":"JWT"}'
    local now=$(date +%s)
    local payload='{"iss":'$APP_ID',"iat":'$now',"exp":'$((now + 600))'}'
    
    # JWT generation logic here
}

# Get installation token
INSTALLATION_TOKEN=$(curl -X POST \
  -H "Authorization: Bearer $JWT" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/app/installations/$INSTALLATION_ID/access_tokens" | \
  jq -r .token)
```

### GitHub API Error Handling

#### Authentication Errors
```json
{
  "message": "Bad credentials",
  "documentation_url": "https://docs.github.com/rest"
}
```

#### Permission Errors
```json
{
  "message": "Resource not accessible by integration",
  "documentation_url": "https://docs.github.com/rest/reference/actions#create-a-registration-token-for-a-repository"
}
```

#### Rate Limiting
```json
{
  "message": "API rate limit exceeded for user ID 123.",
  "documentation_url": "https://docs.github.com/rest/overview/resources-in-the-rest-api#rate-limiting"
}
```

GitHub provides rate limit headers:
```
X-RateLimit-Limit: 5000
X-RateLimit-Remaining: 4999
X-RateLimit-Reset: 1623456789
X-RateLimit-Used: 1
```

### Security Requirements

#### 1. API Key Security

**Storage Requirements:**
- Store RunPod API keys in GitHub repository secrets
- Never log API keys in plaintext
- Mask API keys in output using GitHub Actions automatic masking
- Use environment variables for runtime access only

**Key Rotation:**
```bash
# Example key validation before use
validate_api_key() {
    local key="$1"
    
    # Check key format
    if [[ ! "$key" =~ ^[A-Za-z0-9+/]+=*$ ]]; then
        echo "ERROR: Invalid API key format"
        return 1
    fi
    
    # Check key length (RunPod keys are typically 44 characters)
    if [[ ${#key} -ne 44 ]]; then
        echo "ERROR: Invalid API key length"
        return 1
    fi
    
    # Test key with API
    local test_response
    test_response=$(curl -s -H "Authorization: Bearer $key" \
        -H "Content-Type: application/json" \
        -d '{"query":"query{myself{id}}"}' \
        "$RUNPOD_API_URL")
    
    if echo "$test_response" | jq -e '.errors' >/dev/null; then
        echo "ERROR: API key validation failed"
        return 1
    fi
    
    return 0
}
```

#### 2. Network Security

**TLS Requirements:**
- All API communication must use HTTPS
- Verify SSL certificates
- Use TLS 1.2 or higher
- Implement certificate pinning for production use

**Connection Security:**
```bash
# Secure curl configuration
make_secure_request() {
    curl --tlsv1.2 \
         --cert-status \
         --fail \
         --silent \
         --show-error \
         "$@"
}
```

#### 3. Data Privacy

**Sensitive Data Handling:**
- Mask runner tokens in logs
- Secure cleanup of temporary files containing secrets  
- Use secure memory for sensitive operations
- Implement secure data destruction

**Data Masking Example:**
```bash
mask_sensitive_data() {
    local input="$1"
    
    # Mask RunPod API keys
    input=$(echo "$input" | sed -E 's/([A-Za-z0-9+/]{20})[A-Za-z0-9+/=]*([A-Za-z0-9+/=]{4})/\1***\2/g')
    
    # Mask GitHub tokens
    input=$(echo "$input" | sed -E 's/(gh[ps]_[A-Za-z0-9]{4})[A-Za-z0-9]*([A-Za-z0-9]{4})/\1***\2/g')
    
    echo "$input"
}
```

### Performance Optimization

#### 1. Request Batching
```graphql
# Batch multiple operations
{
  pod1: pod(input: {podId: "pod-123"}) { id desiredStatus }
  pod2: pod(input: {podId: "pod-456"}) { id desiredStatus }
  gpuTypes { id displayName }
}
```

#### 2. Response Caching
```bash
# Cache GPU type information (changes infrequently)
CACHE_DIR="$HOME/.cache/runpod"
GPU_TYPES_CACHE="$CACHE_DIR/gpu_types.json"
CACHE_TTL=3600  # 1 hour

get_gpu_types() {
    # Check cache freshness
    if [[ -f "$GPU_TYPES_CACHE" ]]; then
        local cache_age=$(($(date +%s) - $(stat -c %Y "$GPU_TYPES_CACHE")))
        if [[ $cache_age -lt $CACHE_TTL ]]; then
            cat "$GPU_TYPES_CACHE"
            return 0
        fi
    fi
    
    # Fetch fresh data
    local gpu_types
    gpu_types=$(make_api_request 'query{gpuTypes{id displayName memoryInGb}}')
    
    # Cache result
    mkdir -p "$CACHE_DIR"
    echo "$gpu_types" > "$GPU_TYPES_CACHE"
    echo "$gpu_types"
}
```

#### 3. Connection Reuse
```bash
# Use HTTP keep-alive for multiple requests
export CURL_OPTS="--keepalive-time 60"

# Connection pooling for curl
make_pooled_request() {
    curl $CURL_OPTS \
         --unix-socket /tmp/curl-pool \
         "$@"
}
```

### Monitoring and Observability

#### 1. API Metrics Collection
```bash
# Track API performance metrics
track_api_metrics() {
    local operation="$1"
    local start_time=$(date +%s.%N)
    
    # Make API call
    local result=$?
    
    local end_time=$(date +%s.%N)
    local duration=$(echo "$end_time - $start_time" | bc)
    
    # Log metrics
    echo "metric.api.duration,$operation,$duration,$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> api_metrics.log
    echo "metric.api.success,$operation,$result,$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> api_metrics.log
}
```

#### 2. Error Rate Monitoring
```bash
# Track error rates by type
track_error_rate() {
    local error_type="$1"
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    
    echo "error,$error_type,$timestamp" >> error_metrics.log
    
    # Alert if error rate exceeds threshold
    local recent_errors=$(grep "error,$error_type" error_metrics.log | \
                         tail -100 | wc -l)
    
    if [[ $recent_errors -gt 10 ]]; then
        echo "ALERT: High error rate for $error_type: $recent_errors/100"
    fi
}
```

### Integration Testing Requirements

#### 1. API Integration Tests
```bash
# Test suite for API operations
test_api_integration() {
    echo "=== API Integration Tests ==="
    
    # Test authentication
    test_authentication || return 1
    
    # Test pod creation with minimal resources
    local test_pod_id
    test_pod_id=$(test_pod_creation) || return 1
    
    # Test pod status query
    test_pod_status "$test_pod_id" || return 1
    
    # Test pod cleanup
    test_pod_cleanup "$test_pod_id" || return 1
    
    echo "✓ All API integration tests passed"
}

test_authentication() {
    local auth_response
    auth_response=$(make_api_request 'query{myself{id}}')
    
    if echo "$auth_response" | jq -e '.errors' >/dev/null; then
        echo "✗ Authentication test failed"
        return 1
    fi
    
    echo "✓ Authentication test passed"
}
```

#### 2. Error Handling Tests
```bash
# Test error handling scenarios
test_error_handling() {
    echo "=== Error Handling Tests ==="
    
    # Test invalid API key
    RUNPOD_API_KEY="invalid" test_invalid_auth || return 1
    
    # Test network timeout
    test_network_timeout || return 1
    
    # Test malformed requests
    test_malformed_requests || return 1
    
    echo "✓ All error handling tests passed"
}
```

This comprehensive API integration specification provides the foundation for robust and secure integration with both RunPod and GitHub APIs, ensuring reliable operation under various conditions and proper error handling throughout the system.