# Integration Guide

## Policy Overview

**Current Policy: Ignore-Only System**

flake-readme now uses a simplified ignore-only policy where:
- **ALL directories require readme.nix** unless explicitly ignored
- **Root directory (".")**  now requires readme.nix (changed from previous .nix-only logic)
- **examples/ directories** are ignored by default in both core-docs and flake-module
- **Only exclusion mechanism**: ignore patterns (no special documentable detection)

For complete system capabilities and scope, see the main [README.md](../README.md). For schema requirements, see [Schema Reference](schema.md).

### Key Changes from Previous Versions

**Before:** .nix-only documentable detection
- Only directories containing .nix files (excluding readme.nix) required documentation
- Complex logic to determine "documentable" directories
- Root directory had special handling

**After:** Ignore-only policy
- Simple rule: All directories need readme.nix unless ignored
- Ignore patterns are the only exclusion mechanism
- Consistent behavior across all directories including root

For detailed change history and impact assessment, see [CHANGELOG.md](../CHANGELOG.md).

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

## Directory Requirements Under Ignore-Only Policy

### Root Directory Requirement

**Important Change**: The root directory (".") now requires readme.nix under the ignore-only policy:

```bash
# This will now fail validation:
myproject/
├── flake.nix
├── lib/
│   ├── core.nix
│   └── readme.nix
# Missing: readme.nix at root level
```

```bash
# Correct structure:
myproject/
├── flake.nix
├── readme.nix          # Required at root level
├── lib/
│   ├── core.nix
│   └── readme.nix
```

### examples/ Directory Policy

**Default Behavior**: examples/ directories are automatically ignored to prevent invalid samples from requiring documentation:

```
myproject/
├── readme.nix          # Root documentation (required)
├── lib/
│   ├── core.nix
│   └── readme.nix      # Library documentation (required)
└── examples/           # Automatically ignored - no readme.nix needed
    ├── basic/
    │   └── main.nix    # No readme.nix required in examples/
    └── advanced/
        └── demo.nix    # No readme.nix required in examples/
```

**Override Examples Ignoring** (if you want examples documented):

```nix
# In flake.nix perSystem configuration
readme = {
  enable = true;
  # Remove "examples" from default ignore list
  ignoreExtra = [];  # Only add other directories you want to ignore
};

# Then you'd need:
examples/
├── readme.nix          # Now required
├── basic/
│   ├── main.nix
│   └── readme.nix      # Now required
└── advanced/
    ├── demo.nix
    └── readme.nix      # Now required
```

## Best Practices

### Directory Structure Under Ignore-Only Policy

Under the ignore-only system, ALL directories require readme.nix unless explicitly ignored:

```
myproject/
├── flake.nix
├── readme.nix          # Required (root directory)
├── lib/
│   ├── core.nix
│   └── readme.nix      # Required (all directories need docs)
├── src/
│   ├── main.nix
│   └── readme.nix      # Required (all directories need docs)
├── tests/
│   ├── unit/
│   │   ├── test.nix
│   │   └── readme.nix  # Required (unless tests/ is ignored)
│   └── readme.nix      # Required (unless tests/ is ignored)
└── examples/           # Ignored by default - no readme.nix needed
    └── basic/
        └── main.nix
```

### Ignoring Directories

**Primary Exclusion Mechanism**: Use `ignoreExtra` to exclude directories from readme.nix requirements:

```nix
# Common ignore patterns
readme = {
  enable = true;
  ignoreExtra = [
    "docs"          # Documentation directories
    "build"         # Build output
    "dist"          # Distribution files
    "test-data"     # Test fixtures
    "temp"          # Temporary directories
    "cache"         # Cache directories
    "artifacts"     # Build artifacts
  ];
};
```

**Default Ignored Directories**:
```nix
# These are ignored by default (no need to add to ignoreExtra):
[
  ".git" ".direnv" "node_modules" "result"
  "dist" "target" ".cache" "examples"
]
```



### CI Integration

Add to your CI workflow:
```yaml
- name: Check documentation
  run: nix flake check
```

The `readme.enable = true` configuration automatically adds documentation checks to your flake's check outputs.

Note: `nix flake check` also runs `checks.invalid-examples` which verifies that validation logic correctly detects errors in the invalid samples (success = detection works).

### Migration from .nix-only to Ignore-Only Policy

**If migrating from an older version**, you may encounter new validation requirements:

**Before (old .nix-only logic)**:
```bash
# Only directories with .nix files needed readme.nix
myproject/
├── flake.nix           # Root didn't always require readme.nix
├── lib/                # Required readme.nix (has .nix files)
│   ├── core.nix
│   └── readme.nix
└── docs/               # Didn't require readme.nix (no .nix files)
    └── guide.md
```

**After (ignore-only policy)**:
```bash
# ALL directories require readme.nix unless ignored
myproject/
├── flake.nix
├── readme.nix          # Now required at root
├── lib/
│   ├── core.nix
│   └── readme.nix      # Still required
└── docs/               # Now requires readme.nix OR needs to be ignored
    ├── guide.md
    └── readme.nix      # Either add this...
```

**Migration Strategy**:
```nix
# Option 1: Add readme.nix to newly required directories
# Option 2: Ignore directories that shouldn't need documentation
readme = {
  enable = true;
  ignoreExtra = [ "docs" "build" "temp" ];  # Ignore non-code directories
};
```

## Troubleshooting

### Policy-Related Issues

**Issue**: "Root directory now requires readme.nix"
```json
{
  "missingReadmes": ["."],
  "errorCount": 1
}
```

**Solution**: Create readme.nix at the project root:
```bash
nix run github:your-org/flake-readme#readme-init
```

**Issue**: "examples/ directories requiring readme.nix unexpectedly"

This happens if you've overridden the default ignore list. Examples are ignored by default.

**Solutions**:
```nix
# Ensure examples is in your ignore list
readme = {
  enable = true;
  ignoreExtra = [ "examples" "other-dirs" ];  # Explicitly ignore examples if overriding defaults
};
```

**Issue**: "More directories requiring documentation than expected"

Under ignore-only policy, ALL directories need readme.nix unless explicitly ignored.

**Solutions**:
```bash
# Identify which directories need readme.nix
nix run github:your-org/flake-readme#readme-check

# Add ignore patterns for non-code directories
```

```nix
readme = {
  enable = true;
  ignoreExtra = [
    "test-data" "fixtures" "temp" "cache"
    "build" "artifacts" "docs"
  ];
};
```

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

**Policy-Related Errors**:
- `missing-readme/` - Directory without readme.nix file (now applies to ALL directories unless ignored)
- Root directory missing readme.nix (new requirement under ignore-only policy)

**Schema-Related Errors** (see [invalid examples](../examples/invalid/)):
- `missing-description.nix` - Missing required description field
- `empty-goal.nix` - Empty goal array (not allowed)
- `empty-nongoal.nix` - Empty nonGoal array (not allowed)
- `invalid-goal-type.nix` - Wrong data type for goal field
- `unknown-output-keys.nix` - Unknown keys in output section

For comprehensive error examples and validation patterns, see the [Learning Pathway](../examples/LEARNING_PATHWAY.md) and [invalid examples](../examples/invalid/) directory.

**Note**: Invalid examples are excluded from the main project's validation checks by the default `examples` ignore pattern.