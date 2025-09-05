# RunPod SSH Flake - Responsibility Matrix

## Component Responsibility Overview

This document defines the precise boundaries of responsibility for each component in the RunPod SSH Flake system, ensuring clear separation of concerns and avoiding overlap.

## Responsibility Matrix

| Component | Primary Responsibility | Secondary Responsibilities | Forbidden Responsibilities |
|-----------|----------------------|---------------------------|---------------------------|
| **runpod-client** | RunPod GraphQL API communication | Authentication, response validation, error classification | SSH operations, runner management, state persistence |
| **runpod-ssh** | SSH connection lifecycle | Connection pooling, command execution, file transfer | API communication, runner installation, pod creation |
| **runner-installer** | GitHub Actions runner lifecycle | Service management, dependency installation, health monitoring | Pod management, SSH connection establishment, API calls |
| **pod-lifecycle-manager** | Pod state coordination | Status tracking, inventory management, cleanup orchestration | Direct API calls, SSH operations, runner configuration |
| **workflow-orchestrator** | Cross-component coordination | Error recovery, progress reporting, resource cleanup | Direct component implementation, API communication |
| **configuration-manager** | System configuration | Environment validation, default management, secret handling | Business logic, API operations, SSH connections |

## Detailed Responsibility Breakdown

### RunPod Client (`runpod-client`)

#### ✅ Primary Responsibilities
- Execute GraphQL mutations and queries against RunPod API
- Handle API authentication with Bearer tokens
- Parse and validate GraphQL responses
- Classify and report API-specific errors
- Implement retry logic for network failures
- Manage API rate limiting and backoff strategies

#### ✅ Secondary Responsibilities  
- Validate API key format and basic authentication
- Parse GraphQL error messages into standardized formats
- Handle network connectivity issues with appropriate error codes
- Log API request/response cycles for debugging
- Implement timeout handling for API calls
- Cache API responses when appropriate

#### ❌ Forbidden Responsibilities
- Establishing SSH connections to pods
- Installing or managing GitHub Actions runners
- Tracking pod state beyond API responses
- Managing local configuration files
- Orchestrating multi-component workflows
- Handling SSH authentication or key management

### SSH Manager (`runpod-ssh`)

#### ✅ Primary Responsibilities
- Establish and maintain SSH connections to RunPod instances
- Execute commands over SSH with proper error handling
- Manage SSH connection pooling and reuse
- Handle SSH authentication (key-based and password)
- Implement connection retry logic with exponential backoff
- Manage SSH session cleanup and termination

#### ✅ Secondary Responsibilities
- Transfer files to/from RunPod instances via SCP/SFTP
- Validate SSH connectivity before command execution
- Handle SSH-specific timeouts and connection parameters
- Manage known hosts for ephemeral instances
- Log SSH operations for debugging and auditing
- Implement interactive SSH session management

#### ❌ Forbidden Responsibilities
- Making direct calls to RunPod GraphQL API
- Installing or configuring GitHub Actions runners
- Managing pod lifecycle or state tracking
- Handling GitHub authentication or tokens
- Orchestrating multi-step workflows
- Managing system-wide configuration

### Runner Installer (`runner-installer`)

#### ✅ Primary Responsibilities
- Download and install GitHub Actions runner software
- Configure runners with repository and authentication tokens
- Manage runner service lifecycle (start, stop, restart)
- Handle runner registration and deregistration with GitHub
- Monitor runner health and service status
- Clean up runner files and configuration on removal

#### ✅ Secondary Responsibilities
- Install runner dependencies (Docker, build tools, etc.)
- Create and manage systemd services for runner processes
- Handle runner token validation and refresh
- Implement fallback to manual runner management
- Monitor runner logs and report status
- Handle runner updates and version management

#### ❌ Forbidden Responsibilities
- Establishing SSH connections (delegates to runpod-ssh)
- Creating or managing RunPod instances
- Making direct API calls to RunPod or GitHub APIs
- Managing pod state or inventory tracking
- Handling system-wide configuration management
- Orchestrating workflows across multiple components

### Pod Lifecycle Manager (`pod-lifecycle-manager`)

#### ✅ Primary Responsibilities
- Coordinate pod state transitions across the system
- Maintain local inventory of pod information and status
- Track pod lifecycle events and state changes
- Provide unified pod status information from multiple sources
- Manage pod cleanup and resource deallocation
- Implement pod readiness checking and validation

#### ✅ Secondary Responsibilities
- Cache pod information to reduce API calls
- Validate pod configurations before creation requests
- Generate pod usage reports and statistics
- Handle pod state persistence across system restarts
- Implement pod filtering and search capabilities
- Track pod costs and resource utilization

#### ❌ Forbidden Responsibilities
- Making direct GraphQL API calls (delegates to runpod-client)
- Establishing SSH connections (delegates to runpod-ssh)
- Installing runners (delegates to runner-installer)
- Managing GitHub authentication or tokens
- Handling system-wide configuration
- Implementing retry logic for API calls

### Workflow Orchestrator (`workflow-orchestrator`)

#### ✅ Primary Responsibilities
- Coordinate end-to-end workflows across all components
- Implement error recovery and fallback strategies
- Provide comprehensive progress reporting and status updates
- Handle workflow state management and persistence
- Orchestrate parallel operations and resource management
- Implement comprehensive cleanup on workflow failures

#### ✅ Secondary Responsibilities
- Parse and validate workflow configuration files
- Implement workflow templates and reusable patterns
- Handle workflow scheduling and queuing
- Provide workflow metrics and performance monitoring
- Implement workflow rollback and recovery procedures
- Generate comprehensive workflow execution reports

#### ❌ Forbidden Responsibilities
- Direct implementation of component functionality
- Making API calls to RunPod or GitHub directly
- Establishing SSH connections directly
- Installing runners directly
- Managing low-level configuration details
- Implementing component-specific retry logic

### Configuration Manager (`configuration-manager`)

#### ✅ Primary Responsibilities
- Validate required environment variables and configuration
- Provide default values for optional configuration parameters
- Merge configuration from multiple sources (env, files, defaults)
- Handle sensitive configuration data and secrets management
- Export validated configuration for component consumption
- Implement configuration schema validation

#### ✅ Secondary Responsibilities
- Provide configuration templates and examples
- Handle configuration file format conversion
- Implement configuration inheritance and overrides
- Validate configuration compatibility across components
- Provide configuration documentation and help
- Handle configuration backup and restore

#### ❌ Forbidden Responsibilities
- Implementing business logic or workflows
- Making API calls to external services
- Establishing network connections
- Managing component-specific state
- Implementing retry or recovery logic
- Handling component-specific error conditions

## Communication Protocols

### Component Interaction Rules

#### 1. API Communication Chain
```
workflow-orchestrator → pod-lifecycle-manager → runpod-client → RunPod API
```
- Only `runpod-client` makes direct API calls
- `pod-lifecycle-manager` coordinates all API operations
- `workflow-orchestrator` requests operations through `pod-lifecycle-manager`

#### 2. SSH Operation Chain
```
workflow-orchestrator → runner-installer → runpod-ssh → Pod Instance
```
- Only `runpod-ssh` establishes SSH connections
- `runner-installer` executes commands through `runpod-ssh`
- `workflow-orchestrator` coordinates SSH operations through `runner-installer`

#### 3. Configuration Access Chain
```
All Components → configuration-manager → Environment/Files
```
- All components request configuration through `configuration-manager`
- No component accesses environment variables directly
- Configuration validation is centralized

### Error Handling Responsibilities

#### Component-Level Error Handling
| Component | Error Types Handled | Error Reporting Format | Escalation Path |
|-----------|-------------------|----------------------|----------------|
| `runpod-client` | API errors, network failures, authentication | JSON with error code, message, details | Return to caller with exit code |
| `runpod-ssh` | SSH connection, authentication, command execution | Structured text with error category | Return to caller with exit code |
| `runner-installer` | Installation, service management, GitHub API | JSON with operation, status, error message | Log error, return to caller |
| `pod-lifecycle-manager` | State inconsistencies, validation failures | JSON with pod ID, operation, error | Log error, update state, escalate |
| `workflow-orchestrator` | Coordination failures, timeout errors | Detailed workflow status with failure point | Log comprehensive error, cleanup |
| `configuration-manager` | Validation, missing configuration | Structured error with missing/invalid items | Fail fast with clear error message |

### Dependency Relationships

#### Direct Dependencies
- `workflow-orchestrator` depends on all other components
- `pod-lifecycle-manager` depends on `runpod-client` and `configuration-manager`
- `runner-installer` depends on `runpod-ssh` and `configuration-manager`
- `runpod-ssh` depends on `runpod-client` (for connection info) and `configuration-manager`
- `runpod-client` depends only on `configuration-manager`
- `configuration-manager` has no dependencies

#### Forbidden Dependencies
- No component may directly depend on `workflow-orchestrator`
- Components may not bypass their designated delegates (e.g., `runner-installer` cannot call `runpod-client` directly)
- No circular dependencies are allowed
- Components cannot access other components' internal state directly

### Data Ownership Boundaries

#### Component Data Ownership
| Component | Owns | Reads | Updates | Never Touches |
|-----------|------|-------|---------|---------------|
| `runpod-client` | API responses, authentication state | Configuration | API cache | Pod inventory, runner state |
| `runpod-ssh` | Connection pool, session state | Pod connection info | Connection cache | Pod state, runner config |
| `runner-installer` | Runner configurations, service state | SSH connection status | Runner inventory | Pod state, API responses |
| `pod-lifecycle-manager` | Pod inventory, state tracking | API responses | Pod state cache | SSH sessions, runner state |
| `workflow-orchestrator` | Workflow state, execution logs | All component outputs | Workflow cache | Component internal state |
| `configuration-manager` | Configuration cache, validation results | Environment, files | Configuration state | Business logic state |

### Security Boundaries

#### Component Security Responsibilities
| Component | Security Scope | Sensitive Data Handled | Security Controls |
|-----------|---------------|----------------------|-------------------|
| `runpod-client` | API authentication | RunPod API keys | Token masking, secure headers |
| `runpod-ssh` | SSH authentication | SSH keys, passwords | Key file permissions, connection encryption |
| `runner-installer` | GitHub authentication | Runner tokens | Token masking, secure cleanup |
| `pod-lifecycle-manager` | State integrity | Pod connection info | Data validation, secure storage |
| `workflow-orchestrator` | Workflow security | Aggregated sensitive data | Secure cleanup, audit logging |
| `configuration-manager` | Configuration security | All system secrets | Secret validation, secure defaults |

#### Security Isolation Rules
- Components cannot access other components' credentials directly
- Sensitive data is passed through secure interfaces only
- Components must implement secure cleanup of sensitive data
- All inter-component communication must be auditable
- No component may bypass security controls of other components

## Compliance and Validation

### Responsibility Compliance Checklist

#### For Component Implementers
- [ ] Component only implements functions within its primary responsibility scope
- [ ] All secondary responsibilities are clearly documented as optional/supportive
- [ ] No forbidden responsibilities are implemented
- [ ] All dependencies go through designated interfaces
- [ ] Error handling follows component-specific patterns
- [ ] Security boundaries are respected and maintained

#### For Integration Testing
- [ ] Components communicate only through defined interfaces
- [ ] No component bypasses others' designated responsibilities
- [ ] Error propagation follows defined escalation paths
- [ ] Data ownership boundaries are maintained
- [ ] Security isolation is preserved
- [ ] Performance targets are met within responsibility scope

### Violation Detection and Resolution

#### Common Responsibility Violations
1. **Direct API Access**: Components other than `runpod-client` making RunPod API calls
2. **SSH Bypass**: Components establishing SSH connections without using `runpod-ssh`
3. **State Pollution**: Components modifying state they don't own
4. **Security Bypass**: Components accessing credentials outside their security scope
5. **Workflow Implementation**: Components implementing orchestration logic

#### Resolution Procedures
1. **Identify Violation**: Use dependency analysis and code review
2. **Determine Correct Component**: Reference this responsibility matrix
3. **Refactor Interface**: Create proper component interface if missing
4. **Move Implementation**: Transfer code to correct component
5. **Update Tests**: Ensure tests validate responsibility boundaries
6. **Document Changes**: Update component documentation

This responsibility matrix serves as the definitive guide for maintaining clean architecture and preventing component responsibility overlap in the RunPod SSH Flake system.