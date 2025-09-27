# Contract Validation Examples

This directory contains contract examples organized into basic and anti-pattern categories that demonstrate the CUE Contract Management System's validation capabilities.

## Directory Structure

```
contracts/examples/
├── basic/                    # ✅ Valid contract examples
│   └── contract.cue         # Well-formed API service contract
└── anti-patterns/           # ❌ Validation failure examples (educational)
    ├── duplicates/          # Namespace/name collision examples
    │   ├── service1/contract.cue
    │   └── service2/contract.cue
    └── unresolved-deps/     # Missing dependency examples
        └── frontend/contract.cue
```

## Example Categories

### 1. 🟢 Basic Contract (`basic/`)

**Purpose**: Demonstrate a well-formed, syntactically valid contract.

**Contract**: `corp.example/api-service`
- **Provides**: HTTP API on port 8080
- **Dependencies**: PostgreSQL database (`corp.example/postgres`)
- **Role**: `service`
- **Features**: Proper schema compliance, clear dependency specification

**Validation Result**: ✅ PASS (Individual validation)
- Contract follows schema correctly
- All required fields present
- Proper dependency specification format

### 2. 🟡 Anti-Pattern: Duplicates (`anti-patterns/duplicates/`)

**Purpose**: Demonstrate duplicate namespace/name detection for educational purposes.

**Contracts**:
- **Service 1** (`corp.example/duplicate-service`) in `service1/contract.cue`
  - Provides: HTTP API on port 8081
  - Role: `service`

- **Service 2** (`corp.example/duplicate-service`) in `service2/contract.cue` ⚠️ **DUPLICATE**
  - Provides: Different HTTP API on port 9090
  - Role: `service`

**Validation Result**: ❌ FAIL (Expected in aggregate validation)
- Duplicate namespace/name: `corp.example/duplicate-service`
- Would be caught by aggregate validation with error: "aggregate: duplicate namespace/name found"

### 3. 🔴 Anti-Pattern: Unresolved Dependencies (`anti-patterns/unresolved-deps/`)

**Purpose**: Demonstrate missing dependency detection for educational purposes.

**Contract**: `corp.example/web-frontend` in `frontend/contract.cue`
- **Provides**: Web frontend on port 3000
- **Dependencies**:
  - `corp.example/nonexistent-api` ❌ **MISSING**
  - `corp.example/missing-auth-service` ❌ **MISSING**
- **Role**: `app`

**Validation Result**: ❌ FAIL (Expected in aggregate validation)
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
nix develop --command cue vet contracts/examples/basic/contract.cue

# Test individual anti-pattern examples
nix develop --command cue vet contracts/examples/anti-patterns/duplicates/service1/contract.cue
nix develop --command cue vet contracts/examples/anti-patterns/unresolved-deps/frontend/contract.cue

# Test aggregate validation (includes all contracts - will fail on anti-patterns)
nix flake check

# Run comprehensive example tests
./tools/test-examples.sh
```

## Contract Dependencies Visualization

### Basic Example Structure
```
┌─────────────────┐
│   PostgreSQL    │ (External dependency referenced)
│   (postgres)    │
│                 │
└─────────┬───────┘
          │
          │ (required)
          │
┌─────────▼───────┐
│   API Service   │
│ (api-service)   │
│   Port: 8080    │
└─────────────────┘
```

### Anti-Pattern Examples Structure
```
Duplicates Issue:
┌─────────────────┐    ┌─────────────────┐
│   Service 1     │    │   Service 2     │
│ (duplicate...)  │ ❌ │ (duplicate...)  │  Same namespace/name!
│   Port: 8081    │    │   Port: 9090    │
└─────────────────┘    └─────────────────┘

Unresolved Dependencies:
┌─────────────────┐    ┌─────────────────┐
│ nonexistent-api │ ❌ │missing-auth-... │ ❌  Missing providers!
│                 │    │                 │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          │ (required)           │ (required)
          │                      │
          └──────────┬───────────┘
                     │
            ┌─────────▼───────┐
            │  Web Frontend   │
            │ (web-frontend)  │
            │   Port: 3000    │
            └─────────────────┘
```

This demonstrates the SSOT (Single Source of Truth) principle where contract definitions enable automatic validation of complex microservice ecosystems. The anti-patterns show how the system catches common integration issues during validation.