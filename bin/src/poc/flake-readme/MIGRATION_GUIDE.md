# Migration Guide: Simplified flake-readme System

## Overview

flake-readme has been simplified to use only Git-standard behavior and .nix-only documentable detection. This provides the same core functionality with significantly reduced complexity.

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