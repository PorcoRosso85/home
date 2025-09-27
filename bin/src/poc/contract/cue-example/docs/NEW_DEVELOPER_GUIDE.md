# New Developer Getting Started Guide

## Prerequisites

Before starting, ensure you have:

1. **Nix with flakes enabled**:
   ```bash
   # Check if flakes are enabled
   nix --version
   # Should show Nix 2.4+ with flakes support
   ```

2. **Git repository access**:
   ```bash
   git clone <repository-url>
   cd cue-example
   ```

## Quick Start (5 minutes)

### 1. Enter Development Environment

```bash
# Enter the Nix development shell
nix develop

# You should see:
# =' CUE Contract Management System
# Available commands:
#   cue fmt ./...      - Format CUE files
#   cue vet ./...      - Validate CUE files
#   cue export ./...   - Export CUE to JSON
#   nix flake check    - Run all checks
#   pre-commit run --all-files - Run pre-commit hooks
```

### 2. Verify System Health

```bash
# Run all validation checks
nix flake check

# Should show:
# ✅ All checks passing
```

### 3. Install Pre-commit Hooks

```bash
# Install git hooks for automatic validation
pre-commit install

# Test hooks work
echo "# test" >> README.md
git add README.md
git commit -m "test"  # Should run all hooks automatically
git reset HEAD~1  # Undo test commit
```

## Understanding the System

### Contract Structure

Every contract must be in a `contract.cue` file under `contracts/`:

```cue
package myservice

import "example.corp/contract-system/schema"

MyService: schema.#Contract & {
    namespace: "corp.example"      // Your organization domain
    name:      "my-service"        // Unique service name
    role:      "service"           // service|lib|infra|app|tool
    version:   "1.0.0"            // SemVer

    provides: [{                   // What this service offers
        kind: "http"
        port: 8080
        protocol: "https"
        scope: "public"
    }]

    dependsOn: [{                  // What this service needs
        kind: "db"
        target: "corp.example/postgres"
        versionRange: "^1.0.0"
    }]

    description: "My awesome service"
    tags: ["web", "api"]
}
```

### Key Validation Rules

1. **Uniqueness**: `namespace + name` must be unique across all contracts
2. **Dependencies**: All `dependsOn.target` must reference existing contracts
3. **Schema**: All fields must follow the closed schema (no extra fields)
4. **Secrets**: No plaintext secrets in `secrets/` directory

## Creating Your First Contract

### Step 1: Create Directory Structure

```bash
mkdir -p contracts/myorg/myservice
```

### Step 2: Write Contract

```bash
cat > contracts/myorg/myservice/contract.cue << 'EOF'
package myservice

import "example.corp/contract-system/schema"

MyService: schema.#Contract & {
    namespace: "myorg.example"
    name:      "hello-world"
    role:      "service"
    version:   "1.0.0"

    provides: [{
        kind: "http"
        port: 3000
        protocol: "http"
        scope: "public"
        description: "Hello World API"
    }]

    dependsOn: []

    description: "Simple hello world service"
    tags: ["demo", "http"]
}
EOF
```

### Step 3: Validate

```bash
# Format the contract
cue fmt contracts/myorg/myservice/contract.cue

# Validate syntax
cue vet contracts/myorg/myservice/contract.cue

# Run full system validation
nix flake check
```

### Step 4: Commit

```bash
git add contracts/myorg/myservice/contract.cue
git commit -m "Add hello-world service contract"
```

## Testing and Validation

### Individual Contract Testing

```bash
# Test specific contract
cue vet contracts/myorg/myservice/contract.cue

# Export to JSON
cue export contracts/myorg/myservice/contract.cue
```

### System-wide Testing

```bash
# Run all checks
nix flake check

# Test pre-commit hooks
./tools/test-precommit.sh

# Test secrets detection
./tools/test-secrets.sh

# Test validation examples
./tools/test-examples.sh
```

### Understanding Validation Errors

#### Duplicate Contract Error
```
aggregate: duplicate namespace/name found
```
**Solution**: Ensure `namespace + name` combination is unique.

#### Missing Dependency Error
```
deps: missing provider for corp.example/nonexistent-service
```
**Solution**: Either create the missing service or remove the dependency.

#### Schema Validation Error
```
field not allowed
```
**Solution**: Check that all fields are defined in the schema (closed struct).

#### Secrets Detection Error
```
secrets: plaintext detected in: secrets/config.yaml
```
**Solution**: Encrypt with SOPS or move to `.example` file.

## Advanced Usage

### Working with Examples

Study the three example sets:

```bash
# Normal (valid) contracts
ls contracts/examples/normal/
# Shows: api/, cache/, database/ - proper dependency chain

# Duplicate contracts (validation error)
ls contracts/examples/duplicate/
# Shows: service1/, service2/ - same namespace/name

# Unresolved dependencies (validation error)
ls contracts/examples/unresolved/
# Shows: frontend/ - depends on missing services
```

### Secrets Management

```bash
# Example directory structure
secrets/
├── .sops.yaml              # SOPS configuration
├── production.yaml         # SOPS-encrypted (safe)
└── config.yaml.example     # Template (safe)
```

### Pre-commit Hooks

The system includes these automatic checks:
- **cue-fmt**: Formats CUE files
- **cue-vet**: Validates CUE syntax
- **flake-check**: Full system validation
- **secrets-check**: Detects plaintext secrets
- **shellcheck**: Validates shell scripts
- **nixpkgs-fmt**: Formats Nix files

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure you're in the project root with `cue.mod/module.cue`
2. **Nix not found**: Install Nix with flakes support
3. **Pre-commit not working**: Run `pre-commit install` in project root
4. **Validation hanging**: Check for circular dependencies

### Getting Help

1. **Check logs**: Use `nix log <derivation>` for detailed error information
2. **Test incrementally**: Validate individual contracts before system-wide checks
3. **Study examples**: Look at `contracts/examples/` for working patterns
4. **Read schemas**: Check `schema/contract.cue` for available fields

## Development Workflow

1. **Start**: `nix develop` (enter development environment)
2. **Create**: Write contract in `contracts/org/service/contract.cue`
3. **Validate**: `cue vet <file>` and `nix flake check`
4. **Format**: `cue fmt <file>` or let pre-commit do it
5. **Commit**: Pre-commit hooks run automatically
6. **Review**: CI runs the same checks in PR
7. **Deploy**: Merge after all checks pass

This ensures consistent, validated contracts across your entire system!