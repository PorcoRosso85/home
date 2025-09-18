# Integration Guide

## Quick Start for New Projects

1. **Initialize readme.nix:**
```bash
# Replace 'your-org/flake-readme' with the actual repository path
nix run github:your-org/flake-readme#readme-init
```

2. **Edit the generated readme.nix with your project details**

3. **Verify your documentation:**
```bash
# Replace 'your-org/flake-readme' with the actual repository path
nix run github:your-org/flake-readme#readme-check
```

## Integration with Existing Projects

### Using flake-parts

Add to your `flake.nix`:
```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    # Replace 'your-org/flake-readme' with the actual repository path
    flake-readme.url = "github:your-org/flake-readme";
  };

  outputs = inputs@{ flake-parts, flake-readme, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        flake-readme.flakeModules.readme
      ];
      
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      
      perSystem = {
        # Enable readme.nix validation - that's it!
        readme.enable = true;
        
         # Optional configuration
         # readme = {
         #   enable = true;
         #   root = ./.;
         #   ignoreExtra = [ "build" "dist" ];
         #   policy = {
         #     strict = false;
         #     driftMode = "none";        # Note: Currently not implemented (no warnings/failures)
         #     failOnUnknownOutputKeys = false;
         #   };
         # };
      };
    };
}
```



## Error Examples

**Missing readme.nix:**
```json
{
  "missingReadmes": [".", "src", "lib"],
  "errorCount": 3
}
```

**Invalid schema:**
```json
{
  "reports": {
    ".": {
      "errors": [
        "Missing meta at .",
        "output must be an attrset at ."
      ]
    }
  }
}
```

## Best Practices

### Directory Structure

Ensure every directory with implementation files has a readme.nix:
```
myproject/
├── flake.nix
├── readme.nix          # Root documentation
├── lib/
│   ├── core.nix
│   └── readme.nix      # Library documentation
└── examples/
    ├── basic/
    │   ├── main.nix
    │   └── readme.nix  # Example documentation
    └── readme.nix      # Examples overview
```

### Ignoring Directories

If you need to ignore the `docs/` directory (or others) from readme.nix requirements:

**With flake-parts:**
```nix
readme = {
  enable = true;
  ignoreExtra = [ "docs" "build" "dist" ];
};
```



### CI Integration

Add to your CI workflow:
```yaml
- name: Check documentation
  run: nix flake check
```

The `readme.enable = true` configuration automatically adds documentation checks to your flake's check outputs.

Note: `nix flake check` also runs `checks.invalid-examples` which verifies that validation logic correctly detects errors in the invalid samples (success = detection works).

## Troubleshooting

### Cross-Project CLI Usage

**Issue**: Using CLI commands from other projects fails unexpectedly
```bash
# From different directory
cd /other/project
nix run github:your-org/flake-readme#readme-check  # May fail
```

**Solutions**:
```bash
# Option 1: Use absolute paths
nix run github:your-org/flake-readme#readme-check -- --root /path/to/target/project

# Option 2: Navigate to target directory first
cd /path/to/target/project
nix run github:your-org/flake-readme#readme-check

# Option 3: Use flake reference with path
nix run github:your-org/flake-readme#readme-check /path/to/target/project
```

### Syntax Errors with Mixed Files

**Issue**: Some readme.nix files have syntax errors while others are valid
```
error: syntax error at readme.nix:5:12
```

**Solutions**:
```bash
# Check syntax before validation
find . -name "readme.nix" -exec nix-instantiate --parse {} \; 2>&1 | grep -B1 "error:"

# Fix syntax errors one by one
nix-instantiate --parse ./problematic/readme.nix  # Shows specific error location

# Skip problematic directories temporarily
readme = {
  enable = true;
  ignoreExtra = [ "broken-syntax-dir" ];  # Temporary exclusion
};
```

### Test Data Exclusion Patterns

**Issue**: Test directories like `test-readmes/` trigger validation requirements
```bash
# Common test directory patterns that should be excluded
test-readmes/
tests/fixtures/
examples/test-data/
```

**Solutions**:
```nix
# In flake.nix perSystem configuration
readme = {
  enable = true;
  ignoreExtra = [ 
    "test-readmes"      # Test readme collections
    "test-data"         # Test fixture data
    "fixtures"          # Test fixtures
    "mock-data"         # Mock data directories
    ".test"             # Hidden test directories
  ];
};
```

```bash
# Or use .gitignore for permanent exclusion
echo "test-readmes/" >> .gitignore
git rm -r --cached test-readmes/  # Remove from tracking
git commit -m "Exclude test data from readme validation"
```

### Common Validation Errors

Check the [invalid examples](../examples/invalid/) directory for patterns:

- `missing-description.nix` - Missing required description field
- `empty-goal.nix` - Empty goal array (not allowed)
- `empty-nongoal.nix` - Empty nonGoal array (not allowed) 
- `invalid-goal-type.nix` - Wrong data type for goal field
- `unknown-output-keys.nix` - Unknown keys in output section
- `missing-readme/` - Directory without readme.nix file

These examples demonstrate validation failures and help you understand error messages. Note: Invalid examples are excluded from the main project's validation checks.