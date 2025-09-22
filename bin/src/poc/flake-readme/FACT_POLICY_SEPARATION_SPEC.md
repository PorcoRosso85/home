# Fact-Policy Separation Specification

## Value Statement (WHY)

**Core Problem**: Current documentation conflates facts (what the system observes) with policies (what the system requires). This creates confusion about:
- What is technically possible vs. what is recommended
- What behaviors are hardcoded vs. configurable
- What requirements are absolute vs. policy-driven

**Value of Separation**:
1. **Clarity**: Users understand what is system behavior vs. design choice
2. **Flexibility**: Policies can be changed without affecting factual system capabilities
3. **Maintainability**: Facts remain stable while policies can evolve
4. **Debugging**: Issues can be categorized as fact-collection problems vs. policy-application problems

## Current State Analysis

### Mixed Fact-Policy Examples in README.md:

**Line 81-84 (Policy presented as fact):**
```markdown
**2. .nix-only Documentable Detection:**
- Only directories containing `.nix` files (other than `readme.nix`) require documentation
- Binary/image/build artifact directories are automatically excluded
- Focuses documentation effort where it matters most
```

**Problems**:
- "Only directories containing .nix files require documentation" - This is a POLICY, not a fact
- "Automatically excluded" - Implies hardcoded behavior when it's actually policy-driven
- "Where it matters most" - Value judgment embedded in technical description

### Proper Fact-Policy Separation

**FACTS (System Capabilities)**:
- System can detect all directories in Git-tracked set
- System can read directory contents and identify file types
- System can apply ignore patterns to exclude directories
- System can validate readme.nix files when present

**POLICIES (Design Choices)**:
- Documentation is REQUIRED for directories containing .nix files (configurable via isDocumentable logic)
- Documentation is OPTIONAL for directories without .nix files
- Certain directories are IGNORED by default (configurable via defaultIgnore)
- Missing documentation generates ERRORS (vs. warnings)

## Proposed Terminology

### Current Problematic Terms:
- ".nix-only Documentable Detection" → Implies technical limitation
- "Automatically excluded" → Implies hardcoded behavior
- "Smart filtering" → Vague and subjective

### Improved Fact-Based Terms:
- "Collection Phase" → Facts: What directories exist and what they contain
- "Policy Phase" → Decisions: Which directories require documentation
- "Ignore Patterns" → Configuration: User-controllable exclusions
- "Requirement Rules" → Logic: Configurable criteria for mandatory documentation

## Implementation Impact

This separation allows:
1. **Collection logic** to focus purely on file system facts
2. **Policy logic** to make requirement decisions based on facts
3. **Configuration** to override policy defaults without changing facts
4. **Documentation** to clearly distinguish capability from choice

## Next Steps

1. Update README.md to separate fact descriptions from policy explanations
2. Refactor code comments to distinguish fact-collection from policy-application
3. Create clear user documentation about what can be configured vs. what is fixed
4. Ensure error messages distinguish between fact-collection failures and policy violations