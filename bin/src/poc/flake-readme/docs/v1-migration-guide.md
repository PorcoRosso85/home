# v1 Extension Field Warnings - Migration Guide

## Overview

This guide helps you understand and respond to the new v1 extension field warnings introduced in flake-readme. These warnings help maintain schema consistency while preserving backward compatibility.

## What Are Extension Field Warnings?

Extension field warnings occur when your v1 `readme.nix` file contains top-level fields that aren't part of the official v1 schema specification.

### Official v1 Schema Fields
The v1 schema officially supports only these top-level fields:
- `description` - Project summary (required)
- `goal` - Array of project goals (required)  
- `nonGoal` - Array of non-goals (required)
- `meta` - Metadata object (required)
- `output` - Output declarations (required)
- `source` - Source information (optional)

### Common Extension Fields
Fields that commonly trigger warnings:
- `usage` - Usage examples or documentation
- `features` - Feature lists
- `techStack` - Technology stack information
- `dependencies` - Dependency information
- `examples` - Example configurations
- `roadmap` - Future plans

## Impact Assessment

### Who Is Affected?

1. **Not Affected**: Users with standard v1 documents following the official schema
2. **Low Impact**: Users with extension fields who don't use `strict=true`
3. **Moderate Impact**: Users with `strict=true` who have extension fields

### Warning vs Error Behavior

| Configuration | Extension Fields Present | Behavior |
|---------------|-------------------------|----------|
| Default | Yes | ⚠️ Warnings shown, validation passes |
| Default | No | ✅ No warnings, validation passes |
| `strict=true` | Yes | ❌ Warnings become errors, validation fails |
| `strict=true` | No | ✅ No warnings, validation passes |

## Migration Strategies

### Strategy 1: Move to Meta Field (Recommended)

Move extension fields into the `meta` object:

```nix
# Before (generates warnings)
{
  description = "My awesome project";
  goal = [ "provide great functionality" ];
  nonGoal = [ "be everything to everyone" ];
  meta = {
    owner = [ "@team-name" ];
    lifecycle = "stable";
  };
  output = {
    packages = [ "my-package" ];
  };
  
  # These generate warnings
  usage = "See examples/ directory for usage patterns";
  features = [ "fast" "reliable" "extensible" ];
  techStack = {
    language = "nix";
    framework = "flake-parts";
    tools = [ "nixpkgs-fmt" "statix" ];
  };
}

# After (no warnings)
{
  description = "My awesome project";
  goal = [ "provide great functionality" ];
  nonGoal = [ "be everything to everyone" ];
  meta = {
    owner = [ "@team-name" ];
    lifecycle = "stable";
    
    # Extension fields moved here
    usage = "See examples/ directory for usage patterns";
    features = [ "fast" "reliable" "extensible" ];
    techStack = {
      language = "nix";
      framework = "flake-parts";
      tools = [ "nixpkgs-fmt" "statix" ];
    };
  };
  output = {
    packages = [ "my-package" ];
  };
}
```

**Benefits**:
- ✅ Eliminates warnings
- ✅ Preserves all information
- ✅ Future-compatible
- ✅ Works with `strict=true`

### Strategy 2: Remove Extension Fields

Simply remove fields that aren't essential:

```nix
# Before
{
  description = "My project";
  goal = [ "core functionality" ];
  nonGoal = [ "peripheral features" ];
  meta = { lifecycle = "stable"; };
  output = { packages = []; };
  
  # Remove these if not essential
  internalNote = "This is just for developers";
  temporaryFlag = true;
}

# After  
{
  description = "My project";
  goal = [ "core functionality" ];
  nonGoal = [ "peripheral features" ];
  meta = { lifecycle = "stable"; };
  output = { packages = []; };
}
```

**Benefits**:
- ✅ Clean, specification-compliant document
- ✅ No warnings
- ✅ Minimal maintenance

**Trade-offs**:
- ⚠️ Loses information that might be useful

### Strategy 3: Accept Warnings (Temporary)

Keep extension fields and accept warnings if:
- You're experimenting with future schema features
- The information is valuable but not urgent to migrate
- You're planning to migrate later

**Requirements**:
- ✅ Must not use `strict=true`
- ⚠️ Warnings will appear in validation output
- ⚠️ Extension fields are preserved but marked as non-standard

### Strategy 4: Move to External Documentation

Move extension information to separate documentation files:

```nix
# readme.nix (clean v1)
{
  description = "My project";
  goal = [ "core functionality" ];
  nonGoal = [ "peripheral features" ];
  meta = { 
    lifecycle = "stable";
    documentation = "See USAGE.md for detailed examples";
  };
  output = { packages = []; };
}
```

Create separate files:
- `USAGE.md` - Usage examples
- `FEATURES.md` - Feature documentation  
- `TECH_STACK.md` - Technology stack details

## Quick Migration Commands

### 1. Find Extension Fields

```bash
# Check what warnings you're getting
nix flake check 2>&1 | grep "Unknown keys found"
```

### 2. Identify Affected Files

```bash
# Run validation to see all warnings
nix run .#readme-check
```

### 3. Validate Migration

```bash
# After making changes, verify warnings are gone
nix flake check

# Or for detailed output
nix run .#readme-check
```

## Configuration Options

### Adjusting Strictness

If you want to temporarily disable strict enforcement:

```nix
# In your flake.nix
{
  imports = [ inputs.flake-readme.flakeModules.default ];
  
  flake-readme = {
    enable = true;
    strict = false;  # Allow warnings without failure
  };
}
```

### Per-Project Policies

You can configure different policies for different projects:

```nix
flake-readme = {
  enable = true;
  strict = true;  # Enforce strict validation
  # Other policy options...
};
```

## Troubleshooting

### Common Issues

**Issue**: Getting warnings but validation still passes
- **Cause**: Normal behavior - warnings don't fail validation
- **Solution**: Use Strategy 1 (move to meta) or Strategy 2 (remove fields)

**Issue**: Validation failing with `strict=true`
- **Cause**: Warnings become errors in strict mode  
- **Solution**: Migrate extension fields or set `strict=false` temporarily

**Issue**: Extension fields disappeared from output
- **Cause**: This was the old behavior (before warnings)
- **Solution**: Fields are now preserved in `extra` field for inspection

### Getting Help

1. **Check Examples**: Review `examples/invalid/v1-extension-fields.nix` for guidance
2. **Validation Output**: Use `nix run .#readme-check` for detailed warnings
3. **Schema Reference**: See `docs/schema.md` for complete specification

## Best Practices

1. **Follow the Official Schema**: Stick to the documented v1 fields when possible
2. **Use Meta for Extensions**: When you need additional fields, put them in `meta`
3. **Document Your Choices**: Use comments to explain why certain fields are in `meta`
4. **Regular Validation**: Run `nix flake check` regularly to catch issues early
5. **Gradual Migration**: You don't need to migrate everything at once - warnings don't break builds

## Future Considerations

- Future schema versions may officially support currently "extension" fields
- Extension fields help inform future schema evolution
- The warning system preserves compatibility while encouraging best practices
- Migration paths will be provided for future schema upgrades