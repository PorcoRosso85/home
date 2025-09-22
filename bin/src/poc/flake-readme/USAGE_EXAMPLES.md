# flake-readme Usage Examples

## Basic Usage (ignore-only policy)

### 1. Simple Project Setup
```nix
# In your flake.nix
{
  inputs.flake-readme.url = "github:user/flake-readme";

  outputs = { self, nixpkgs, flake-parts, flake-readme }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [ flake-readme.flakeModules.readme ];

      perSystem = {
        readme.enable = true;  # Enables ignore-only policy
      };
    };
}
```

### 2. Custom Ignore Patterns
```nix
perSystem.readme = {
  enable = true;
  ignoreExtra = [
    "temp"           # Ignore temp/ directory
    "experiments"    # Ignore experiments/ directory
    "build-cache"    # Ignore build-cache/ directory
  ];
};
```

### 3. Understanding Missing Detection
With ignore-only policy, these directories WILL require readme.nix:
- `src/` - Source code directory
- `tools/` - Utility tools directory
- `docs/` - Documentation directory (unless ignored)
- `scripts/` - Script directory

These directories are ignored by default:
- `.git/` - Git repository data
- `examples/` - Example code (often broken samples)
- `node_modules/` - Node.js dependencies
- `result/` - Nix build results

## Troubleshooting

### "Too many missing readmes"
**Problem**: Your project has many directories without readme.nix
**Solutions**:
1. Add ignoreExtra for directories that don't need documentation
2. Create minimal readme.nix files for important directories
3. Use `git rm --cached` to stop tracking unwanted directories

### "Examples directory requires readme"
**Problem**: You want to document your examples/ directory
**Solution**: Remove "examples" from ignore list
```nix
perSystem.readme = {
  enable = true;
  # Don't ignore examples - it will now require readme.nix
  ignoreExtra = [];  # Or specify other dirs to ignore
};
```