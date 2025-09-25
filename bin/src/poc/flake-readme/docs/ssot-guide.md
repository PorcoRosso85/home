# SSOT Guide: Single Source of Truth for Documentation

## Overview

The SSOT (Single Source of Truth) system ensures consistency between `readme.nix` (structured data) and `README.md` (narrative documentation) by preventing duplication through automated verification.

## Architecture

```
readme.nix (SSOT)  →  README.md (narrative)
     ↑                       ↑
 structured data      natural language
 machine-readable     human-readable
     facts              usage guide
```

## Principles

1. **readme.nix**: Contains structured, machine-readable project metadata
2. **README.md**: Contains narrative, usage-focused documentation
3. **No Duplication**: Exact content copying between files is prohibited
4. **Automated Verification**: CI checks enforce these rules automatically

## SSOT Rules

### ✅ Allowed in README.md
- Natural language descriptions (different from readme.nix exact text)
- Usage examples and tutorials
- Links to readme.nix for detailed specifications
- Installation and setup instructions

### ❌ Prohibited in README.md
- Exact duplication of readme.nix `description` field
- Structured data patterns like `goal = [...]`, `meta = {...}`
- Hardcoded version numbers (use readme.nix version instead)
- Schema documentation (belongs in separate docs or readme.nix)

## Verification Commands

### Manual Check
```bash
# Run SSOT verification locally
./scripts/ssot-verify.sh

# Or use the simple lint script
./scripts/readme-lint.sh
```

### CI Integration
```bash
# SSOT check is automatically run with all checks
nix flake check

# Run SSOT check specifically
nix build .#checks.x86_64-linux.ssot-check
```

## Best Practices

### 1. Division of Responsibility
- **readme.nix**: What the project IS (facts, metadata, schema)
- **README.md**: How to USE the project (examples, tutorials, guides)

### 2. Cross-References
```markdown
<!-- In README.md -->
For detailed technical specifications, see [readme.nix](./readme.nix).
```

### 3. Version Handling
```markdown
<!-- ❌ Bad: Hardcoded version -->
This is version 2.1.0 of the project.

<!-- ✅ Good: Reference to SSOT -->
Current version information is maintained in [readme.nix](./readme.nix).
```

### 4. Natural Language Variation
```nix
# readme.nix
description = "Pure Nix core that collects and validates readme.nix";
```

```markdown
<!-- README.md - Use different wording -->
A lightweight documentation collection system built in pure Nix.
```

## Error Resolution

### "Exact description duplication detected"
- **Problem**: README.md contains the exact text from readme.nix `description`
- **Fix**: Rewrite the README.md description in your own words

### "Structured data patterns found"
- **Problem**: README.md contains `goal = [...]` or similar structures
- **Fix**: Move structured data to readme.nix, keep narrative in README.md

### "README.md should reference readme.nix"
- **Suggestion**: Add a link to readme.nix for users who need technical details

## Integration Example

```nix
# flake.nix
{
  inputs.flake-readme.url = "github:your-org/flake-readme";

  outputs = { flake-parts, flake-readme, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [ flake-readme.flakeModules.readme ];

      perSystem = {
        readme.enable = true;  # Enables both readme.nix validation AND SSOT checking
      };
    };
}
```

## Benefits

1. **DRY Principle**: Eliminates manual synchronization between structured and narrative docs
2. **Automated Quality**: CI prevents documentation drift
3. **Clear Separation**: Each file has distinct, well-defined responsibilities
4. **Developer Experience**: Simple rules, automated enforcement
5. **Maintainability**: Changes in one place don't require manual updates elsewhere

---

*This SSOT system implements the Single Responsibility Principle at the documentation level, ensuring clean separation between facts (readme.nix) and narrative (README.md).*