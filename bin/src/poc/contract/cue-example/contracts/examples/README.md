# Contract Validation Examples

This directory contains three sets of contract examples that demonstrate the CUE Contract Management System's validation capabilities.

## Example Sets

### 1. 🟢 Normal Contracts (`normal/`)

**Purpose**: Demonstrate a complete, valid contract system with proper dependencies.

**Contracts**:
- **Database Service** (`corp.example/postgres-db`)
  - Provides: PostgreSQL database on port 5432
  - Dependencies: None (infrastructure service)
  - Role: `infra`

- **Cache Service** (`corp.example/redis-cache`)
  - Provides: Redis cache on port 6379
  - Dependencies: None (infrastructure service)
  - Role: `infra`

- **API Service** (`corp.example/user-api`)
  - Provides: HTTP API on port 8080
  - Dependencies: Database (required) + Cache (optional)
  - Role: `service`

**Validation Result**: ✅ PASS
- All contracts have unique namespace/name combinations
- All dependencies are resolved (database and cache exist)
- Proper dependency chain: API → Database + Cache

### 2. 🟡 Duplicate Contracts (`duplicate/`)

**Purpose**: Demonstrate duplicate namespace/name detection.

**Contracts**:
- **Service 1** (`corp.example/duplicate-service`)
  - Provides: HTTP API on port 8081
  - Role: `service`

- **Service 2** (`corp.example/duplicate-service`) ⚠️ **DUPLICATE**
  - Provides: gRPC API on port 9090
  - Role: `service`

**Validation Result**: ❌ FAIL (Expected)
- Duplicate namespace/name: `corp.example/duplicate-service`
- Would be caught by aggregate validation with error: "aggregate: duplicate namespace/name found"

### 3. 🔴 Unresolved Dependencies (`unresolved/`)

**Purpose**: Demonstrate missing dependency detection.

**Contracts**:
- **Frontend Service** (`corp.example/web-frontend`)
  - Provides: Web frontend on port 3000
  - Dependencies:
    - `corp.example/nonexistent-api` ❌ **MISSING**
    - `corp.example/missing-auth-service` ❌ **MISSING**
  - Role: `app`

**Validation Result**: ❌ FAIL (Expected)
- Missing dependencies: `corp.example/nonexistent-api`, `corp.example/missing-auth-service`
- Would be caught by aggregate validation with error: "deps: missing provider for corp.example/nonexistent-api, corp.example/missing-auth-service"

## Validation System Demonstration

These examples prove that the CUE Contract Management System correctly:

1. ✅ **Validates individual contract syntax** using CUE schema enforcement
2. ✅ **Detects duplicate namespace/name combinations** in aggregate validation
3. ✅ **Identifies unresolved dependencies** across the contract ecosystem
4. ✅ **Provides standardized error messages** for debugging
5. ✅ **Maintains proper separation of concerns** between infrastructure, services, and applications

## Usage

To validate these examples:

```bash
# Test individual contract syntax
nix develop --command cue vet contracts/examples/normal/api/contract.cue

# Test aggregate validation (includes all contracts)
nix flake check

# Run comprehensive example tests
./tools/test-examples.sh
```

## Contract Dependencies Visualization

```
Normal Example Flow:
┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     Redis       │
│ (postgres-db)   │    │ (redis-cache)   │
│   Port: 5432    │    │   Port: 6379    │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          │ (required)           │ (optional)
          │                      │
          └──────────┬───────────┘
                     │
            ┌─────────▼───────┐
            │    User API     │
            │   (user-api)    │
            │   Port: 8080    │
            └─────────────────┘
```

This demonstrates the SSOT (Single Source of Truth) principle where contract definitions enable automatic validation of complex microservice ecosystems.