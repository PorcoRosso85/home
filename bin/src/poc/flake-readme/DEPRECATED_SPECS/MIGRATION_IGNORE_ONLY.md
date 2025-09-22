# Migration to ignore-only Policy

## What Changed
flake-readme now uses **ignore-only policy**: ALL directories require `readme.nix` unless explicitly ignored.

## Before vs After

### Before (nix-only detection)
- Only directories with .nix files required documentation
- Documentation was optional for non-Nix directories

### After (ignore-only policy)
- ALL directories require documentation unless ignored
- More comprehensive documentation coverage
- Clearer, predictable rules

## Migration Steps

### 1. Check current missing
```bash
nix eval .#index.missingReadmes
```

### 2. Choose approach for each missing directory

**Option A: Add documentation**
```nix
# Create readme.nix in the directory
{
  description = "Purpose of this directory";
  goal = ["What this directory achieves"];
  nonGoal = ["What this directory doesn't do"];
  meta = {};
  output = {};
}
```

**Option B: Ignore the directory**
```nix
perSystem.readme = {
  enable = true;
  ignoreExtra = ["unwanted-dir"];
};
```

**Option C: Remove from Git tracking**
```bash
git rm --cached -r unwanted-dir/
echo "unwanted-dir/" >> .gitignore
git commit -m "Stop tracking unwanted-dir"
```

### 3. Verify changes
```bash
nix flake check
nix eval .#index.missingReadmes  # Should be empty or acceptable
```