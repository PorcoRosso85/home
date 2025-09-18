# Git Tracking Specification and Limitations

## Core Principle: self.outPath as Git Tracking Set Snapshot

**SPECIFICATION**: `inputs.self.outPath` = **Git tracking set snapshot** at flake evaluation time.

- **NOT**: .gitignore parsing or filesystem walking
- **IS**: Exact replica of Git's tracked file set (git ls-tree equivalent)
- **BEHAVIOR**: Untracked files/directories are invisible to Nix evaluation
- **GUARANTEE**: Pure functional behavior - same Git state produces identical results

## Summary

The `inputs.self.outPath` mechanism provides **Git tracking set filtering**, not complete .gitignore parsing. This has specific success cases and important limitations.

## ✅ Success Cases (Verified)

### 1. Untracked Directory Exclusion
- **Behavior**: Untracked directories are automatically excluded from missing readme checks
- **Verification**: `test-non-nix-dir`, `test-no-readme-marker` etc. don't appear in missing list
- **Mechanism**: Nix flake evaluation only includes Git-tracked file set

### 2. .nix-only Documentable Logic  
- **Behavior**: Only directories with .nix files (other than readme.nix) are considered documentable
- **Verification**: Directories with only binary/image files are ignored
- **Result**: Eliminates "indiscriminate readme requirements"

## ❌ Critical Limitations (Proven)

### 1. Tracked-then-Ignored Files NOT Excluded
- **Git Behavior**: Once a file is tracked, .gitignore has no effect
- **Demonstration**: `test-tracked-then-ignored/` appears in missing despite being in .gitignore
- **Root Cause**: Git tracking set ≠ .gitignore parsing
- **Solution**: Use `git rm` to stop tracking, then add to .gitignore

### 2. Flake-External Paths Lose Git Benefits  
- **Limitation**: `root` pointing outside flake boundaries loses Git filtering
- **Scope**: Only applies to `inputs.self.outPath` (flake's own content)
- **Alternative**: Use `ignoreExtra` for name-based exclusions

## 🔧 Recommended Solutions

### For Excluding Tracked Files
```bash
# Stop tracking unwanted directory
git rm -r --cached unwanted-dir/
echo "unwanted-dir/" >> .gitignore
git commit -m "Remove unwanted-dir from tracking"
```

### For Name-based Exclusions
```nix
perSystem.readme = {
  enable = true;
  ignoreExtra = [ "build" "dist" "temp" ];  # Name-based exclusion
};
```

## 📋 Specification Summary

| Aspect | Behavior | Mechanism |
|--------|----------|-----------|
| **Untracked dirs** | ✅ Auto-excluded | Git tracking set filtering |
| **Tracked + .gitignore** | ❌ Still included | Git specification |
| **Flake-external paths** | ❌ No Git filtering | inputs.self.outPath scope |
| **Binary/image dirs** | ✅ Excluded | .nix-only documentable logic |

## 📂 Default Ignore Patterns (Nix Built-in)

### Standard Git/Build Exclusions
```
.git/           # Git metadata (security + performance)
.direnv/        # direnv environment files  
node_modules/   # Node.js dependencies (size + performance)
target/         # Rust build artifacts
dist/           # JavaScript build output
build/          # Generic build directories
```

### Hidden File Handling in Pure Mode
- **Nix Pure Mode**: Only honors built-in exclusions above
- **NO**: Custom .gitignore or .nixignore parsing
- **RATIONALE**: Maintains pure functional evaluation guarantees
- **OVERRIDE**: Use `ignoreExtra` for additional name-based exclusions

## 🔄 Alternative Control Mechanisms

### 1. Git Tracking Control (Primary)
```bash
# Remove mistakenly tracked files
git rm --cached -r unwanted-dir/
echo "unwanted-dir/" >> .gitignore
git commit -m "Stop tracking unwanted-dir"
```

### 2. ignoreExtra Override (Secondary)
```nix
perSystem.readme = {
  enable = true;
  ignoreExtra = [ "experimental" "temp" "build-cache" ];
};
```

## 🎯 Optimal Usage Pattern

1. **Primary**: Rely on Git tracking for most exclusions
2. **Specific**: Use `ignoreExtra` for name-based overrides  
3. **Cleanup**: Use `git rm --cached` for mistakenly tracked files
4. **Scope**: Keep `root = inputs.self.outPath` (default) for Git benefits

## 🚫 Absolute Limitations

### Git Tracking Boundary
- **GUARANTEE**: Only applies within flake boundary (`inputs.self.outPath`)
- **FAILURE**: External paths (`root = /other/path`) lose all Git filtering
- **CONSEQUENCE**: Full filesystem scan without built-in exclusions

### Git Specification Constraints  
- **IMMUTABLE**: Once tracked, files remain in Git set until explicitly removed
- **GITIGNORE LIMIT**: Cannot retroactively exclude already-tracked files
- **SOLUTION**: Use `git rm --cached` to modify tracking set

This specification confirms that Pure Nix + Git tracking provides sufficient functionality for most use cases, eliminating the need for complex fd integration or marker systems.