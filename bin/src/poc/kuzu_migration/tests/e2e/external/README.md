# External CLI Import Tests

This directory contains end-to-end tests that verify the `kuzu-migrate` CLI binary is properly accessible from external flakes.

## Test Coverage

The `test_e2e_cli_import.py` file tests the following scenarios:

1. **Binary Build Availability** (`test_binary_available_via_nix_build`)
   - Verifies that external flakes can build the kuzu-migrate package
   - Checks that the binary exists and is executable

2. **Help Command** (`test_binary_help_command`)
   - Tests that `kuzu-migrate --help` works from external context
   - Verifies help output contains expected commands

3. **Version Command** (`test_binary_version_command`)
   - Tests that `kuzu-migrate --version` displays correctly
   - Verifies version number matches expected value

4. **Direct Nix Run** (`test_nix_run_direct_invocation`)
   - Tests that `nix run .#kuzu-migrate` works from external flakes
   - Verifies the app can be exposed and executed

5. **Library Functions** (`test_library_functions_available`)
   - Tests that `lib.mkKuzuMigration` is accessible
   - Verifies external flakes can use library functions to generate migration apps

6. **Init Command** (`test_init_command_from_external`)
   - Tests that the init command works when invoked externally
   - Verifies DDL directory structure is created correctly

7. **Package Metadata** (`test_package_metadata_exports`)
   - Tests that package metadata is correctly exposed
   - Verifies package name and binary location

8. **Multi-System Support** (`test_multiple_system_support`)
   - Tests that the package works across different Nix systems
   - Verifies system compatibility checks

## Running the Tests

From the project root:

```bash
# Run all external CLI tests
nix develop -c uv run pytest tests/e2e/external/test_e2e_cli_import.py -v

# Run a specific test
nix develop -c uv run pytest tests/e2e/external/test_e2e_cli_import.py::TestCLIBinaryAvailability::test_binary_help_command -v
```

## Test Implementation Details

The tests create temporary external flakes that:
- Import the kuzu-migrate package
- Test various aspects of the CLI
- Clean up after themselves

Each test is self-contained and creates its own temporary directory for testing.