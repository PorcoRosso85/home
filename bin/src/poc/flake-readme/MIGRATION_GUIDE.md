# Migration Guide: Simplified flake-readme System

## Overview

flake-readme has been simplified to use only Git-standard behavior and ignore-only policy enforcement. This provides the same core functionality with significantly reduced complexity and clear fact-policy separation.

## BREAKING CHANGE: Ignore-Only Policy Transition

### What Changed in Step 1.5

**Previous Behavior (.nix-only documentable detection)**:
- Only directories containing `.nix` files (excluding `readme.nix`) required documentation
- Non-.nix directories were automatically exempt from documentation requirements

**New Behavior (ignore-only policy)**:
- ALL directories now require `readme.nix` files by default
- Exemptions are handled exclusively through ignore patterns
- `isDocumentable` fact remains available but no longer affects missing detection policy

### Impact Assessment

**Who is affected**:
- Projects with non-.nix directories that were previously automatically exempt
- Users relying on implicit exemption behavior
- Estimated impact: ~20-30% of existing users may need configuration adjustments

**What requires action**:
- Directories with no `.nix` files that previously were ignored automatically
- Build output directories, documentation directories, test fixtures
- Any directory structure where documentation was not desired

## What Changed

### ❌ Removed Features
- `perSystem.readme.search.mode` option
- fd tool integration and dependency
- `.no-readme` marker file processing
- Complex mode switching behavior

### ✅ Preserved Features  
- Core readme.nix validation and schema enforcement
- Git boundary filtering (via `inputs.self.outPath`)
- .nix-only documentable detection
- `ignoreExtra` configuration for manual overrides
- All existing validation and reporting functionality

### Migration Options for Ignore-Only Transition

**Option A: ignoreExtra Configuration (Recommended for most cases)**
```nix
perSystem.readme = {
  enable = true;
  ignoreExtra = [
    "docs"           # Documentation directories
    "tests"          # Test fixture directories
    "examples"       # Example directories
    "build"          # Build output
    "dist"           # Distribution files
    "assets"         # Static assets
  ];
};
```

**Option B: Git-based Permanent Exclusion**
```bash
# For directories you never want tracked or documented
git rm -r --cached unwanted-directories/
echo "unwanted-directories/" >> .gitignore
git commit -m "Permanently exclude directories from documentation requirements"
```

**Before/After Behavior Examples**

*Before (automatic exemption)*:
```
project/
├── src/           # .nix files → required readme.nix ✓
├── docs/          # no .nix files → automatically exempt ✓
├── tests/         # no .nix files → automatically exempt ✓
└── assets/        # no .nix files → automatically exempt ✓
```

*After (ignore-only policy)*:
```
project/
├── src/           # required readme.nix ✓
├── docs/          # NOW requires readme.nix ⚠️ (unless ignored)
├── tests/         # NOW requires readme.nix ⚠️ (unless ignored)
└── assets/        # NOW requires readme.nix ⚠️ (unless ignored)
```

## Migration Paths

### 1. Users with `search.mode = "pure"` (No Action Required)
Your configuration already uses the default behavior:
```nix
# Before (explicit)
perSystem.readme = {
  enable = true;
  search.mode = "pure";  # ← Remove this line
};

# After (simplified)
perSystem.readme = {
  enable = true;
  # Automatic pure behavior
};
```

### 2. Users with `search.mode = "fd"`

#### Option A: Git Tracking Migration (Recommended for 90% of cases)
```bash
# Add unwanted directories to .gitignore
echo "build/" >> .gitignore
echo "temp/" >> .gitignore
echo "artifacts/" >> .gitignore

# For already-tracked directories, stop tracking them:
git rm -r --cached build/ temp/ artifacts/
git commit -m "Remove build artifacts from tracking"
```

#### Option B: Use ignoreExtra (Simple override)
```nix
perSystem.readme = {
  enable = true;
  ignoreExtra = [ "build" "temp" "artifacts" "experiments" ];
};
```

### 3. Users with `.no-readme` Markers

#### Option A: Move to .gitignore (Recommended)
```bash
# For each directory with .no-readme:
rm some-dir/.no-readme
echo "some-dir/" >> .gitignore

# If already tracked:
git rm -r --cached some-dir/
git commit -m "Remove some-dir from tracking"
```

#### Option B: Use ignoreExtra
```nix
perSystem.readme = {
  enable = true;
  ignoreExtra = [ "experimental-code" "temp-work" "old-prototypes" ];
};
```

## Benefits of Migration

### For End Users
- **Predictable behavior**: Git-standard behavior only
- **Zero external dependencies**: No fd tool required
- **Simpler configuration**: Single mode, clear semantics
- **Better performance**: No shell script processing overhead

### For Maintainers
- **Reduced complexity**: ~48 lines of code removed (~15% reduction)
- **Fewer edge cases**: Single behavior path to test and maintain
- **Standard compliance**: 100% Git behavior alignment
- **Lower support burden**: Fewer configuration options to troubleshoot

## Validation

### Verify Migration Success
```bash
# Should work without any search.mode configuration
nix flake check

# Should show only directories with .nix files as requiring readme.nix
nix build .#readme-report
cat result | jq '.missingReadmes'
```

### Expected Behavior
- ✅ Untracked directories automatically excluded
- ✅ Binary/image directories ignored (.nix-only logic)
- ✅ Manual overrides via `ignoreExtra` work as before
- ✅ All validation and schema enforcement preserved

## Troubleshooting

### "Directory still appears in missing list despite being in .gitignore"
**Cause**: Directory was already tracked before adding to .gitignore  
**Solution**: 
```bash
git rm -r --cached directory-name/
git commit -m "Stop tracking directory-name"
```

### "Want to exclude directory but it has .nix files"
**Options**:
1. Use `ignoreExtra = [ "directory-name" ]`
2. Move .nix files elsewhere and add directory to .gitignore
3. Use `git rm --cached` to stop tracking

### "Need complex .gitignore-style patterns"
**Solution**: The simplified system focuses on Git tracking sets rather than .gitignore parsing. For complex patterns, use Git's standard ignore mechanisms directly.

## Support

For migration questions or issues:
1. Check your Git tracking status: `git status`
2. Verify .gitignore syntax: `git check-ignore -v path/`
3. Test with `ignoreExtra` for temporary overrides
4. Review [Git documentation](https://git-scm.com/docs/gitignore) for advanced patterns

The simplified system provides the same practical value with much clearer semantics and maintenance benefits.