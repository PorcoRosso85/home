# RunPod SSH Flake - System Design Document

## System Overview and Goals

The RunPod SSH Flake is a Nix-based system that provides seamless integration between RunPod GPU instances and GitHub Actions self-hosted runners through secure SSH connections. The primary goal is to enable automated GPU-accelerated CI/CD workflows with dynamic resource provisioning and cost optimization.

### Primary Objectives
1. **Dynamic GPU Resource Provisioning**: On-demand creation and management of GPU instances
2. **Automated CI/CD Integration**: Seamless GitHub Actions runner deployment and management  
3. **Cost Optimization**: Intelligent pod lifecycle management with bid pricing strategies
4. **Security**: Secure SSH connections with proper authentication and cleanup
5. **Reliability**: Robust error handling and retry mechanisms
6. **Scalability**: Support for multiple concurrent runners and job matrices

### Target Use Cases
- GPU-accelerated model training in CI/CD pipelines
- Large-scale distributed computing workloads
- Cost-effective GPU access for development teams
- Ephemeral compute environments for testing

## Component Responsibility Matrix

| Component | Primary Responsibility | Secondary Responsibilities |
|-----------|----------------------|---------------------------|
| `runpod-client` | RunPod GraphQL API communication | Authentication, error handling, response parsing |
| `runpod-ssh` | SSH connection management | Connection pooling, retry logic, session management |
| `runner-installer` | GitHub Actions runner lifecycle | Installation, configuration, monitoring, cleanup |
| `pod-lifecycle-manager` | Pod state management | Creation, resumption, stopping, status monitoring |
| `workflow-orchestrator` | End-to-end workflow coordination | Component integration, error recovery, reporting |
| `configuration-manager` | System configuration | Environment validation, secret management, defaults |

## Component Specifications

### 1. RunPod Client (`runpod-client`)

#### Single Responsibility
Execute GraphQL operations against the RunPod API with authentication, error handling, and response validation.

#### Interface Contract
```bash
# Input: GraphQL query/mutation, variables, authentication
# Output: Structured JSON response or standardized error format
runpod-client <operation> [variables] [options]
```

#### Key Operations
- `create-pod`: Execute podRentInterruptable mutation
- `resume-pod`: Execute podResume mutation  
- `stop-pod`: Execute podStop mutation
- `get-pod`: Execute pod query with detailed information
- `list-pods`: Execute pods query with filtering options
- `validate-auth`: Test API key validity

#### Error Handling Responsibilities
- Network connectivity failures
- Authentication/authorization errors
- Rate limiting and retry logic
- API response validation
- GraphQL error parsing

### 2. SSH Manager (`runpod-ssh`)

#### Single Responsibility
Establish, maintain, and execute commands over secure SSH connections to RunPod instances.

#### Interface Contract
```bash
# Input: Pod ID, command/operation, SSH parameters
# Output: Command execution results or connection status
runpod-ssh <pod_id> <operation> [command] [options]
```

#### Key Operations
- `connect`: Establish SSH connection with retry logic
- `exec`: Execute single command and return output
- `session`: Start interactive SSH session
- `test-connection`: Validate connectivity and authentication
- `copy-file`: Secure file transfer operations
- `close`: Terminate SSH connections cleanly

#### Connection Management
- Connection pooling and reuse
- Automatic retry with exponential backoff
- SSH key and password authentication support
- Known hosts management for ephemeral instances
- Connection timeout and cleanup

### 3. Runner Installer (`runner-installer`)

#### Single Responsibility
Manage the complete lifecycle of GitHub Actions runners on RunPod instances.

#### Interface Contract
```bash
# Input: Repository URL, token, runner configuration
# Output: Installation status, service state, logs
runner-installer <operation> <repo_url> <token> [options]
```

#### Key Operations
- `install`: Download and configure GitHub Actions runner
- `start`: Start runner service (systemd or manual)
- `stop`: Stop running runner service
- `remove`: Unregister and cleanup runner
- `status`: Get runner service status and health
- `logs`: Retrieve and monitor runner logs

#### Service Management
- Systemd service creation and management
- Manual runner process management (fallback)
- Runner token validation and refresh
- Dependency installation (Docker, tools)
- Health monitoring and restart logic

### 4. Pod Lifecycle Manager (`pod-lifecycle-manager`)

#### Single Responsibility
Coordinate pod state transitions and maintain pod inventory with status tracking.

#### Interface Contract
```bash
# Input: Pod management operation and parameters
# Output: Pod state information and operational results
pod-lifecycle-manager <operation> [pod_id] [parameters]
```

#### Key Operations
- `create`: Create new pod with specified configuration
- `resume`: Resume stopped pod and validate readiness  
- `stop`: Stop running pod gracefully
- `status`: Get comprehensive pod status information
- `list`: List all pods with filtering and sorting
- `wait`: Wait for pod to reach desired state
- `cleanup`: Remove terminated or failed pods

#### State Management
- Pod state tracking and transitions
- Readiness and health checking
- Connection information management
- Resource utilization monitoring
- Cost tracking and reporting

### 5. Workflow Orchestrator (`workflow-orchestrator`)

#### Single Responsibility
Coordinate end-to-end workflows by integrating all components and managing error recovery.

#### Interface Contract
```bash
# Input: Workflow definition, target configuration
# Output: Workflow execution status and comprehensive reporting
workflow-orchestrator <workflow_type> <config_file> [options]
```

#### Key Workflows
- `setup-runner`: Create pod → Wait ready → Install runner → Validate
- `teardown-runner`: Stop runner → Cleanup → Stop pod → Verify cleanup
- `multi-pod-setup`: Parallel pod creation and runner installation
- `health-check`: Comprehensive system health validation
- `cost-report`: Resource usage and cost analysis

#### Coordination Responsibilities
- Component integration and dependency management
- Error recovery and fallback strategies
- Progress reporting and status updates
- Resource cleanup on failure
- Workflow state persistence

### 6. Configuration Manager (`configuration-manager`)

#### Single Responsibility
Manage system configuration, validate environments, and provide default values.

#### Interface Contract
```bash
# Input: Configuration queries and validation requests  
# Output: Configuration values and validation results
configuration-manager <operation> [key] [value]
```

#### Key Operations
- `validate-env`: Check required environment variables
- `get-defaults`: Provide default configuration values
- `merge-config`: Combine multiple configuration sources
- `validate-secrets`: Verify secret availability and format
- `export-env`: Export validated environment for subprocesses

#### Configuration Sources
- Environment variables
- Configuration files (YAML/JSON)
- Default value definitions
- Runtime parameter overrides
- Secret management system integration

## Interface Contracts Between Components

### RunPod Client → SSH Manager
```json
{
  "pod_id": "string",
  "connection_info": {
    "host": "ip_address",
    "port": 22,
    "username": "root"
  },
  "status": "RUNNING|STOPPED|STARTING"
}
```

### SSH Manager → Runner Installer
```json
{
  "connection_status": "connected|failed",
  "session_id": "string",
  "authentication": "success|failure",
  "capabilities": ["docker", "systemd", "curl"]
}
```

### Runner Installer → Pod Lifecycle Manager
```json
{
  "runner_status": "installed|running|stopped|failed",
  "service_name": "actions.runner.service",
  "runner_id": "github_runner_id",
  "logs": "log_output"
}
```

### All Components → Configuration Manager
```json
{
  "request_type": "get|validate|set",
  "key": "configuration_key", 
  "scope": "global|pod|runner",
  "value": "configuration_value"
}
```

## Data Flow Architecture

### 1. Pod Creation Flow
```
User Request → Configuration Manager (validate) → RunPod Client (create) → 
Pod Lifecycle Manager (track) → SSH Manager (test connection) → 
Workflow Orchestrator (report success)
```

### 2. Runner Installation Flow  
```
Workflow Orchestrator (initiate) → SSH Manager (connect) → 
Runner Installer (install + start) → SSH Manager (validate) → 
Pod Lifecycle Manager (update status) → Workflow Orchestrator (complete)
```

### 3. Error Recovery Flow
```
Component (error detected) → Workflow Orchestrator (receive error) →
Configuration Manager (get retry policy) → Failed Component (retry) →
Workflow Orchestrator (escalate/recover) → User (report)
```

### 4. Cleanup Flow
```
Workflow Orchestrator (initiate) → Runner Installer (stop + remove) →
SSH Manager (disconnect) → RunPod Client (stop pod) →
Pod Lifecycle Manager (cleanup state) → Workflow Orchestrator (report)
```

## Architecture Decisions

### 1. Component Communication
- **Decision**: Use command-line interfaces between components
- **Rationale**: Language-agnostic, debuggable, shell-scriptable
- **Trade-offs**: Slower than in-memory APIs, but better isolation

### 2. State Management
- **Decision**: Stateless components with external state tracking
- **Rationale**: Better reliability, easier debugging, simpler scaling
- **Trade-offs**: More complex coordination, potential state inconsistencies

### 3. Error Handling Strategy
- **Decision**: Fail-fast with comprehensive error reporting
- **Rationale**: Quick feedback, easier debugging, prevent resource waste
- **Trade-offs**: Less resilient to transient failures

### 4. Configuration Management
- **Decision**: Environment variables with configuration file overrides
- **Rationale**: 12-factor app compliance, CI/CD friendly, flexible
- **Trade-offs**: More complex precedence rules

### 5. SSH Connection Handling
- **Decision**: Connection pooling with automatic cleanup
- **Rationale**: Performance optimization, resource efficiency
- **Trade-offs**: Added complexity, potential connection state issues

### 6. Authentication Strategy
- **Decision**: API key-based with SSH key fallback
- **Rationale**: Simple integration, secure for ephemeral instances
- **Trade-offs**: Key management complexity

## Security Architecture

### Authentication Flow
1. Environment variable validation (API keys, tokens)
2. RunPod API authentication with bearer token
3. SSH connection with key-based or password authentication
4. GitHub runner token validation and registration

### Security Boundaries
- **API Layer**: RunPod GraphQL API authentication
- **Network Layer**: SSH encrypted connections
- **Process Layer**: Isolated component execution
- **Data Layer**: Secret masking and secure cleanup

### Threat Model
- **API Key Exposure**: Mitigated by environment variable isolation
- **SSH MITM**: Mitigated by connection validation
- **Resource Hijacking**: Mitigated by proper cleanup procedures
- **Cost Abuse**: Mitigated by bid limits and monitoring

## Performance Considerations

### Scalability Targets
- Support for 10+ concurrent pods
- Runner installation under 5 minutes
- SSH command execution under 30 seconds
- Pod creation under 10 minutes (market dependent)

### Optimization Strategies
- **Connection Reuse**: SSH connection pooling
- **Parallel Operations**: Multi-pod job matrices
- **Caching**: Configuration and state caching
- **Async Operations**: Non-blocking command execution

### Resource Limits
- Maximum 50 SSH connections per manager
- Configuration cache TTL of 300 seconds
- Pod status check interval of 30 seconds
- Maximum retry attempts: 5 per operation

## Reliability Design

### Failure Scenarios
1. **API Failures**: Network issues, rate limits, service outages
2. **SSH Failures**: Connection timeouts, authentication failures
3. **Pod Failures**: Instance termination, system crashes
4. **Runner Failures**: Installation errors, service crashes

### Recovery Strategies
1. **Exponential Backoff**: For API and connection retries
2. **Circuit Breakers**: For persistent failure detection
3. **Graceful Degradation**: Fallback to manual processes
4. **State Recovery**: Resume operations from last known state

### Monitoring Requirements
- Component health checks every 60 seconds
- Error rate tracking with alerting thresholds
- Resource utilization monitoring
- Cost tracking and budget alerts

This design document provides the architectural foundation for implementing a robust, scalable, and maintainable RunPod SSH Flake system while maintaining clear separation of concerns and well-defined interfaces between components.