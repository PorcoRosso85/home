# RunPod SSH Flake - System Design Document

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   GitHub        │    │   RunPod         │    │   Pod Instance  │
│   Actions       │────│   GraphQL API    │────│   (GPU Compute) │
│   Workflow      │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌──────────────────┐            │
         │              │  Nix Flake Tools │            │
         └──────────────│  - runpod-client │────────────┘
                        │  - runpod-ssh    │     SSH Connection
                        │  - runner-installer
                        └──────────────────┘
```

### 1.2 Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Nix Flake Layer                       │
├─────────────────┬─────────────────┬─────────────────────────┤
│ runpod-client   │ runpod-ssh      │ runner-installer        │
│ (GraphQL API)   │ (SSH Manager)   │ (GitHub Actions)        │
└─────────────────┴─────────────────┴─────────────────────────┘
         │                   │                   │
┌─────────────────┬─────────────────┬─────────────────────────┐
│ Pod Lifecycle   │ SSH Connection  │ Runner Management       │
│ - Create        │ - Establish     │ - Install               │
│ - Resume        │ - Execute       │ - Configure             │
│ - Stop          │ - Transfer      │ - Monitor               │
│ - Monitor       │ - Session       │ - Cleanup               │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### 1.3 Data Flow

```
1. GitHub Actions Trigger
   ↓
2. API Authentication (RunPod API Key)
   ↓
3. Pod Management (Create/Resume/Stop)
   ↓
4. SSH Connection Establishment
   ↓
5. GitHub Runner Installation
   ↓
6. Workload Execution
   ↓
7. Cleanup and Monitoring
```

## 2. API Integration Design

### 2.1 RunPod GraphQL API

The system integrates with RunPod's GraphQL API using the following operations:

#### Core Mutations
- `podRentInterruptable`: Create new GPU instances
- `podResume`: Resume stopped instances
- `podStop`: Stop running instances

#### Core Queries
- `pod`: Get detailed pod information
- `pods`: List all user pods

#### API Client Design
```bash
graphql_request() {
    local query="$1"
    local variables="${2:-{}}"
    
    curl -s \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $RUNPOD_API_KEY" \
        -d "{\"query\":\"$query\",\"variables\":$variables}" \
        "$RUNPOD_API_URL"
}
```

### 2.2 GitHub API Integration

#### Runner Registration
- Uses GitHub's REST API for runner token generation
- Automated registration and deregistration
- Support for organization and repository-level runners

#### Token Management
```bash
# Token generation
RUNNER_TOKEN=$(curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$REPO/actions/runners/registration-token" | \
  jq -r .token)
```

## 3. Security Architecture

### 3.1 Authentication & Authorization

#### API Key Management
- RunPod API keys stored as GitHub secrets
- Environment variable injection for scripts
- Token masking in GitHub Actions logs

#### SSH Security
- Ephemeral key pairs for pod connections
- StrictHostKeyChecking disabled for dynamic IPs
- UserKnownHostsFile=/dev/null for clean sessions

#### Runner Security
- Runner tokens are short-lived (1 hour default)
- Automatic cleanup on workflow completion
- Isolated runner environments

### 3.2 Network Security

#### Connection Patterns
```
GitHub Actions Runner → SSH (port 22) → RunPod Instance
                    ↑
              Secure tunnel over internet
```

#### Security Controls
- SSH connection timeout settings
- Retry logic with exponential backoff
- Connection validation before operations

## 4. Performance Optimization

### 4.1 Connection Management

#### Connection Pooling
- Reuse SSH connections for multiple operations
- Connection validation before reuse
- Automatic reconnection on failure

#### Retry Strategies
```bash
# Exponential backoff with jitter
retry_with_backoff() {
    local max_retries=$1
    local base_delay=$2
    
    for i in $(seq 1 $max_retries); do
        if execute_operation; then
            return 0
        fi
        
        local delay=$((base_delay * 2**i + RANDOM % 10))
        sleep $delay
    done
}
```

### 4.2 Resource Optimization

#### Pod Lifecycle Management
- Automatic pod suspension when idle
- Smart resumption based on workload patterns
- Cost optimization through bid price strategies

#### Monitoring and Scaling
- Real-time pod status monitoring
- Multi-pod job matrix support
- Load balancing across multiple instances

## 5. Reliability and Error Handling

### 5.1 Error Categories

#### API Errors
- Network connectivity issues
- Authentication failures
- Rate limiting
- Service unavailability

#### SSH Errors
- Connection timeouts
- Authentication failures
- Network partitions
- Pod unavailability

#### Runner Errors
- Installation failures
- Configuration issues
- Service startup problems
- Resource constraints

### 5.2 Error Handling Strategies

#### Graceful Degradation
```bash
# Fallback mechanisms
install_runner_with_fallback() {
    # Try systemd service first
    if ! install_systemd_service; then
        log_warning "Systemd installation failed, trying manual start"
        start_runner_manually
    fi
}
```

#### Circuit Breaker Pattern
- Temporary failure detection
- Automatic service suspension
- Recovery validation

## 6. Monitoring and Observability

### 6.1 Logging Strategy

#### Structured Logging
- Color-coded log levels (INFO, WARNING, ERROR)
- Consistent message formatting
- Context-aware logging

#### Log Aggregation
- GitHub Actions workflow logs
- Pod-level application logs
- SSH session logs

### 6.2 Metrics Collection

#### Performance Metrics
- Pod creation time
- SSH connection establishment time
- Runner installation duration
- Job execution time

#### Reliability Metrics
- Success/failure rates
- Error categorization
- Recovery times

## 7. Cost Optimization

### 7.1 Dynamic Pricing

#### Bid Strategy
- Market-aware bid prices
- Automatic price adjustment
- Cost vs. availability trade-offs

#### Resource Utilization
- Right-sized instance selection
- Automatic scaling based on workload
- Idle resource detection and cleanup

### 7.2 Lifecycle Management

#### Smart Scheduling
```bash
# Cost-aware pod management
manage_pod_lifecycle() {
    local workload_demand=$1
    
    if [[ $workload_demand -gt $SCALE_UP_THRESHOLD ]]; then
        create_additional_pods
    elif [[ $workload_demand -lt $SCALE_DOWN_THRESHOLD ]]; then
        suspend_idle_pods
    fi
}
```

## 8. Extensibility and Integration

### 8.1 Plugin Architecture

#### Custom Hooks
- Pre/post pod creation hooks
- Custom runner installation steps
- Workflow extension points

#### Configuration Management
- Environment-specific configurations
- Template-based pod specifications
- Dynamic parameter injection

### 8.2 Third-Party Integrations

#### Monitoring Systems
- Prometheus metrics export
- Grafana dashboard integration
- Alert manager notifications

#### CI/CD Pipelines
- Jenkins pipeline integration
- GitLab CI/CD support
- Custom webhook handlers

## 9. Development and Testing

### 9.1 Testing Strategy

#### Unit Testing
- Individual function testing
- Mock API responses
- Error condition simulation

#### Integration Testing
- End-to-end workflow testing
- Multi-pod scenarios
- Failure recovery testing

### 9.2 Development Workflow

#### Local Development
```bash
# Development shell
nix develop

# Test individual components
./scripts/pod-lifecycle.sh status test-pod
./scripts/ssh-runner.sh exec test-pod "echo 'test'"
```

#### CI/CD Testing
- Automated workflow validation
- Cost-controlled test environments
- Performance regression testing

## 10. Future Enhancements

### 10.1 Planned Features

#### Advanced Scheduling
- Machine learning-based demand prediction
- Multi-cloud provider support
- Advanced resource allocation algorithms

#### Enhanced Security
- Zero-trust networking
- Hardware security module integration
- Advanced threat detection

### 10.2 Scalability Improvements

#### Horizontal Scaling
- Multi-region deployments
- Load balancer integration
- Global resource management

#### Performance Optimization
- Connection multiplexing
- Async operation support
- Caching strategies

## 11. Deployment Considerations

### 11.1 Environment Setup

#### Prerequisites
- Nix with flakes support
- GitHub repository access
- RunPod account and API access

#### Configuration Management
- Environment-specific secrets
- Feature flag management
- Rollback strategies

### 11.2 Operations

#### Monitoring
- Health check endpoints
- Performance dashboards
- Alert configuration

#### Maintenance
- Automated updates
- Dependency management
- Security patching

This design provides a comprehensive foundation for the RunPod SSH Flake system while maintaining flexibility for future enhancements and integrations.