# KuzuDB Migration Test Execution Guide

## Overview

This guide explains how to set up and run tests for the KuzuDB Migration Framework using Nix flakes and the `nix run .#test` command.

## Test Setup Structure

### 1. Flake Configuration (`flake.nix`)

The flake.nix has been configured with the following key components:

```nix
{
  description = "A development environment for the kuzu_migration project";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        # Development shell with required packages
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            python311
            ruff
            uv
            stdenv.cc.cc.lib  # C++ runtime for KuzuDB
          ];
          
          LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";
        };
        
        # Applications
        apps = {
          # Test runner accessible via: nix run .#test
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib"
              echo "🧪 Running KuzuDB Migration tests..."
              exec ${pkgs.uv}/bin/uv run pytest -v "$@"
            ''}";
          };
        };
      });
}
```

### 2. Key Components Explained

#### Development Shell (`devShells.default`)
- **python311**: Python 3.11 runtime
- **ruff**: Python linter and formatter
- **uv**: Fast Python package manager
- **stdenv.cc.cc.lib**: C++ runtime libraries required by KuzuDB

#### Environment Variables
- **LD_LIBRARY_PATH**: Set to include C++ libraries needed by KuzuDB's native components

#### Test Application (`apps.test`)
- Creates a shell script that:
  1. Sets up the required environment variables
  2. Displays a test banner
  3. Executes pytest through uv with verbose output
  4. Passes any additional arguments to pytest

## Running Tests

### Method 1: Using `nix run`

```bash
# Run all tests
nix run .#test

# Run specific test file
nix run .#test -- test_alter_table_capabilities.py

# Run with pytest options
nix run .#test -- -k "test_add_column" -v

# Run with coverage
nix run .#test -- --cov=. --cov-report=html
```

### Method 2: Using Development Shell

```bash
# Enter development shell
nix develop

# Install dependencies
uv sync

# Run tests directly
uv run pytest -v

# Run specific tests
uv run pytest test_alter_table_capabilities.py -v
```

### Method 3: Using the Test Runner Script

```bash
# Make script executable (if not already)
chmod +x run_tests.sh

# Run tests
./run_tests.sh

# With arguments
./run_tests.sh -k "test_add_column"
```

## Test Files

The project includes the following test files:

1. **test_alter_table_capabilities.py**
   - Tests for KuzuDB's ALTER TABLE functionality
   - Validates column operations (ADD, DROP, RENAME)
   - Checks default values and constraints

## Dependencies Management

### pyproject.toml Configuration

```toml
[project]
name = "kuzu-migration-tool"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    # Production dependencies
]

[project.optional-dependencies]
dev = [
    "pytest",
    # Add other test dependencies here
]
```

### Installing Dependencies

Dependencies are managed by `uv` and installed automatically when running tests via `nix run .#test`.

To manually install:
```bash
uv sync
```

## Troubleshooting

### Common Issues

1. **LD_LIBRARY_PATH errors**
   - Solution: Ensure you're running tests through nix or have set the environment variable
   ```bash
   export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib"
   ```

2. **Module not found errors**
   - Solution: Run `uv sync` to ensure all dependencies are installed

3. **Permission denied on test script**
   - Solution: `chmod +x run_tests.sh`

### Debug Mode

Run tests with increased verbosity:
```bash
nix run .#test -- -vv --tb=short
```

## Best Practices

1. **Always use nix run for consistency**: This ensures the correct environment is set up
2. **Keep tests isolated**: Use temporary databases for each test
3. **Clean up resources**: Ensure temporary files are removed after tests
4. **Use fixtures**: For common setup code across tests

## Example Test Pattern

```python
import tempfile
import kuzu
import pytest

def create_temp_database():
    """Create a temporary database for testing"""
    temp_dir = tempfile.mkdtemp()
    return f"{temp_dir}/test.db"

def test_migration_feature():
    db_path = create_temp_database()
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    # Test implementation
    
    # Cleanup happens automatically when temp_dir goes out of scope
```

## CI/CD Integration

To integrate with CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run tests
  run: nix run .#test
```

## Summary

The `nix run .#test` command provides a consistent, reproducible way to run tests with all required dependencies and environment variables properly configured. This approach ensures that tests run the same way across different machines and environments.