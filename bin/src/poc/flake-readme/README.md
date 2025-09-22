# flake-readme POC

Single-responsibility POC for collecting and validating readme.nix documentation files.

**Requirements**: This library requires [flake-parts](https://flake.parts/) for integration. Manual integration is not supported to maintain simplicity and reduce maintenance burden.

## Quick Start

1. **Initialize readme.nix in your project:**
```bash
# Replace 'your-org/flake-readme' with the actual repository path
nix run github:your-org/flake-readme#readme-init
```

2. **Edit the generated readme.nix with your project details**

3. **Validate your documentation:**
```bash
# Replace 'your-org/flake-readme' with the actual repository path
nix run github:your-org/flake-readme#readme-check
```

4. **Integrate with flake-parts** (see [Integration Guide](docs/integration.md))

## Documentation

- 📋 **[Schema Reference](docs/schema.md)** - Complete v1 schema specification with extension field warnings
- 🔧 **[Integration Guide](docs/integration.md)** - flake-parts integration
- 🚀 **[Migration Guide](docs/v1-migration-guide.md)** - Handle v1 extension field warnings
- 📄 **[CHANGELOG](CHANGELOG.md)** - Recent changes and impact assessment
- 📁 **[Examples](examples/)** - Working examples and patterns
- 🎓 **[Learning Pathway](examples/LEARNING_PATHWAY.md)** - Structured progression from valid to invalid examples
- ❌ **[Invalid Examples](examples/invalid/)** - Common validation errors and warning cases
- ⚠️  **[Extension Field Warnings](examples/invalid/v1-extension-fields.nix)** - Learn about v1 schema extension behavior

## Purpose

This POC provides:
- ✅ Automated readme.nix validation 
- ✅ flake-parts module for easy integration
- ✅ Schema enforcement (description, goal, nonGoal, meta, output)
- ✅ CI-ready checks and reports
- ✅ Git-aware directory filtering (automatic via inputs.self.outPath)

## Scope

### In Scope
- readme.nix file collection and validation
- Schema v1 support with meta/output fields
- flake-parts integration module
- Standalone CLI tools
- Git-aware directory filtering (automatic via flake boundaries)

### Out of Scope  
- Dependency analysis → See `poc/flake-dependency`
- Cross-flake documentation collection
- Combined docs+deps functionality

## Configuration and Features

### Simple Configuration

flake-readme uses a single, predictable behavior based on Git and Nix standards:

```nix
perSystem.readme = {
  enable = true;
  # That's it! All filtering is automatic
};
```

### Automatic Smart Filtering

The system automatically reduces "indiscriminate readme requirements" through:

**1. Git Boundary Filtering:**
- Uses `inputs.self.outPath` (default) to limit scope to Git-tracked content
- Untracked/ignored directories are automatically excluded  
- Follows standard Git behavior - predictable and familiar

**2. Directory Filtering:**
- Only directories containing `.nix` files (other than `readme.nix`) require documentation
- Binary/image/build artifact directories are automatically excluded
- Focuses documentation effort where it matters most

**3. Manual Overrides:**
```nix
perSystem.readme = {
  enable = true;
  ignoreExtra = [ "experimental" "temp" "build-artifacts" ];  # Name-based exclusions
};
```

### Git Integration Details

**How it works:**
- `inputs.self.outPath` provides Git tracking set filtering (not .gitignore parsing)
- Untracked directories → automatically excluded
- Tracked directories → subject to ignore-based filtering logic

**Critical limitations (especially for CLI usage):**
- **Tracked → .gitignore limitation**: Files already tracked remain visible even after adding to `.gitignore` (Git standard behavior)
- **CLI impact**: When using `nix run github:org/flake-readme#readme-check`, this limitation becomes more problematic as remote flakes include all tracked content
- **Root boundary restriction**: CLI tools cannot access files outside the flake's Git root, limiting manual override options

**Required remediation workflow:**
```bash
# BEFORE adding to .gitignore, remove from tracking:
git rm -r --cached unwanted-dir/
echo "unwanted-dir/" >> .gitignore
git commit -m "Remove unwanted-dir from tracking"

# Verify exclusion:
git ls-files | grep unwanted-dir  # Should return nothing
```

**CLI-specific considerations:**
- Remote flake execution operates on the complete tracked set
- Manual path filtering becomes limited when running via `nix run`
- Always verify tracking status before relying on .gitignore for exclusions

### Recommended Operational Patterns

**For excluding problematic directories (test-readmes, build artifacts, etc.):**

1. **Configuration-based exclusion (preferred for flake-parts):**
```nix
perSystem.readme = {
  enable = true;
  ignoreExtra = [ "test-readmes" "build" "dist" "node_modules" ];
};
```

2. **Git-based exclusion (universal approach):**
```bash
# Remove from Git tracking first (critical step)
git rm -r --cached problematic-dir/
echo "problematic-dir/" >> .gitignore
git commit -m "Exclude problematic-dir from documentation requirements"
```

3. **Combined approach for comprehensive coverage:**
```nix
# Handle edge cases and temporary exclusions
perSystem.readme = {
  enable = true;
  ignoreExtra = [ "experimental" "temp" "artifacts" ];
};
```

**Key principle**: Keep `defaultIgnore` minimal and handle specific cases through operational configuration. This maintains KISS/YAGNI principles while providing practical flexibility.

## Error Handling Limitations

### tryEval Technical Constraints

flake-readme uses `builtins.tryEval` for safe error handling, but this has important limitations that affect user experience:

**Parse-time errors (Syntax errors):**
- **Immediate failure**: Syntax errors cannot be aggregated - they fail instantly at parse stage
- **No batch reporting**: Unlike evaluation errors, syntax errors halt processing immediately  
- **Examples**: Missing braces `{`, unclosed strings `"incomplete`, invalid Nix syntax

**Evaluation-time errors (Runtime errors):**
- **Aggregated reporting**: Can be collected and reported together with other validation issues
- **Graceful degradation**: Other files continue processing despite individual failures
- **Examples**: Undefined variables, failed function calls, missing dependencies

**User impact:**
- **Fix syntax first**: Always resolve syntax errors before evaluation errors will be visible
- **Sequential debugging**: Cannot see all error types simultaneously - parse errors mask evaluation errors
- **Tool behavior**: CLI validation stops at first syntax error per file, requiring iterative fixes

**Recommended workflow:**
1. Run validation to identify syntax errors
2. Fix all syntax errors in affected files  
3. Re-run validation to reveal evaluation errors
4. Address evaluation errors and schema validation issues

This is a fundamental Nix limitation, not specific to flake-readme.

## Basic Usage

### CLI Behavior and Requirements

**Important**: The CLI operates exclusively within flake boundaries (Git-tracked file sets). This ensures consistent behavior with flake-parts modules and prevents unexpected file discovery outside project scope.

**Requirements:**
- CLI commands only work in directories containing a `flake.nix` file
- Non-flake directories will not function with CLI tools  
- Behavior is unified with flake-parts integration for predictable operation
- Git tracking determines file visibility (same as `inputs.self.outPath` behavior)

### Commands

```bash
# Run validation checks (requires flake.nix in current/parent directory)
nix flake check

# Build documentation report (via flake-parts integration)
nix build .#readme-report

# View collected docs  
cat result | jq

# Learn from invalid examples (for debugging validation errors)
ls examples/invalid/  # See common validation mistakes

# Understand v1 extension field warnings
cat examples/invalid/v1-extension-fields.nix  # Educational example with comprehensive comments
```

For detailed integration instructions, see [docs/integration.md](docs/integration.md).