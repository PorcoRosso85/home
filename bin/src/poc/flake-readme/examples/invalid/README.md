# Invalid Examples - Learning from Common Validation Errors

This directory contains educational examples that demonstrate common validation errors and edge cases when working with readme.nix files. Each example is designed to help you understand the flake-readme validation system and learn how to fix issues in your own projects.

## Learning Pathway

The examples in this directory follow a structured learning progression:

### 1. Schema Structure Errors
Learn about the fundamental structure requirements of readme.nix documents.

### 2. Field Validation Errors  
Understand how individual fields are validated and what constitutes valid content.

### 3. Warning Cases
See how the system handles edge cases that generate warnings but don't fail validation.

## Examples Overview

### Core Schema Violations

#### [`missing-description.nix`](./missing-description.nix)
**Error Type**: Missing Required Field  
**Learning Focus**: All readme.nix files must have a `description` field  
**Fix**: Add a descriptive string explaining what the project does

#### [`empty-goal.nix`](./empty-goal.nix)  
**Error Type**: Empty Required Field  
**Learning Focus**: `goal` field must contain at least one meaningful item  
**Fix**: Add concrete, actionable goals that describe what the project achieves

#### [`empty-nongoal.nix`](./empty-nongoal.nix)
**Error Type**: Empty Required Field  
**Learning Focus**: `nonGoal` field must contain at least one meaningful item  
**Fix**: Add clear statements about what the project explicitly doesn't do

#### [`invalid-goal-type.nix`](./invalid-goal-type.nix)
**Error Type**: Wrong Data Type  
**Learning Focus**: `goal` and `nonGoal` must be arrays of strings, not strings  
**Fix**: Wrap string values in arrays: `"goal"` → `[ "goal" ]`

### Output Schema Violations

#### [`unknown-output-keys.nix`](./unknown-output-keys.nix)
**Error Type**: Invalid Output Keys  
**Learning Focus**: `output` field has a defined schema with specific allowed keys  
**Fix**: Use only valid output keys: `packages`, `apps`, `modules`, `overlays`, `devShells`

#### [`readme.nix`](./readme.nix)
**Error Type**: Complex validation example  
**Learning Focus**: Multiple validation patterns and edge cases  
**Fix**: See inline comments for specific guidance

### Missing File Structure

#### [`missing-readme/`](./missing-readme/)
**Error Type**: Missing readme.nix file  
**Learning Focus**: Projects integrated with flake-readme must have a readme.nix file  
**Fix**: Create a readme.nix file with the required schema

### Warning Cases (Non-Failing)

#### [`v1-extension-fields.nix`](./v1-extension-fields.nix) ⭐
**Type**: Extension Field Warnings  
**Learning Focus**: Understanding v1 schema extension field behavior  
**When**: You add fields not in the official v1 schema specification  
**Behavior**: 
- ✅ Document validates successfully (not an error)
- ⚠️  Warnings generated for unknown fields  
- 💾 Extension fields preserved in `extra` field
- 📊 `warningCount > 0` in validation output

**Common Extension Fields**:
- `usage` - How to use the project
- `features` - List of project features  
- `techStack` - Technology stack information
- `version` - Version information
- `dependencies` - Dependency information

**Resolution Options**:
1. **Ignore** (if experimenting): Warnings don't block validation
2. **Move to meta** (recommended): Place custom fields in `meta.yourField`  
3. **Remove** (cleanest): Keep only official v1 schema fields
4. **Future migration**: Wait for schema versions that support these fields

## How to Use These Examples

### 1. Understanding Error Messages
Each example demonstrates specific error patterns. Run the validation to see the exact error messages:

```bash
# Test a specific invalid example
nix run .#readme-check -- examples/invalid/empty-goal.nix

# Test all examples (some will fail as expected)
nix flake check
```

### 2. Learning from Fixes
Compare the invalid examples with the valid examples in [`examples/`](../):
- [`examples/application/readme.nix`](../application/readme.nix) - Clean v1 schema
- [`examples/domain/readme.nix`](../domain/readme.nix) - Proper field usage
- [`examples/flake-parts-integration/`](../flake-parts-integration/) - Integration pattern

### 3. Progressive Learning Path
Suggested order for learning:

1. **Start with structure**: `missing-description.nix`, `empty-goal.nix`
2. **Learn field types**: `invalid-goal-type.nix`  
3. **Understand output schema**: `unknown-output-keys.nix`
4. **Explore warnings**: `v1-extension-fields.nix` ⭐
5. **Complex cases**: `readme.nix`, `missing-readme/`

## Common Error Patterns

### Pattern 1: Missing Required Fields
```nix
# ❌ This will fail
{
  goal = [ "do something" ];  # Missing description
}

# ✅ This will pass  
{
  description = "Project description";
  goal = [ "do something" ];
  nonGoal = [ "not do other things" ];
}
```

### Pattern 2: Wrong Data Types
```nix
# ❌ This will fail
{
  description = "Project description";
  goal = "single goal";  # Should be array
}

# ✅ This will pass
{  
  description = "Project description";
  goal = [ "single goal" ];  # Array of strings
}
```

### Pattern 3: Extension Fields (Warnings)
```nix
# ⚠️  This generates warnings but doesn't fail
{
  description = "Project description"; 
  goal = [ "demonstrate warnings" ];
  nonGoal = [ "fail validation" ];
  
  # Extension fields trigger warnings in v1
  features = [ "custom-field" ];  # Warning: unknown field
  usage = "How to use this";      # Warning: unknown field
}

# ✅ This is warning-free
{
  description = "Project description";
  goal = [ "demonstrate clean validation" ];  
  nonGoal = [ "generate any warnings" ];
  meta = {
    # Custom fields go in meta to avoid warnings
    features = [ "custom-field" ];
    usage = "How to use this";
  };
}
```

## Debugging Your Own readme.nix

When you encounter validation errors in your own projects:

1. **Check the error message** - It will tell you exactly what's wrong
2. **Find the matching example** - Look for similar error patterns here
3. **Compare with valid examples** - See how the valid examples handle similar cases
4. **Test incrementally** - Fix one issue at a time and re-validate

## Schema Reference

For complete schema documentation, see:
- [Schema Reference](../../docs/schema.md) - Complete v1 specification
- [Integration Guide](../../docs/integration.md) - How to integrate with flake-parts

## Questions?

If you encounter validation errors not covered by these examples, consider:
- Checking the [Schema Reference](../../docs/schema.md) for detailed field specifications
- Running `nix run .#readme-check -- your-file.nix` for specific error messages
- Looking at the test specification: [`TEST_SPECIFICATION_V1_EXTENSION_WARNINGS.md`](../../TEST_SPECIFICATION_V1_EXTENSION_WARNINGS.md)

Remember: The goal of these examples is to make learning from errors educational rather than frustrating. Each error teaches you something about the schema and how to write better readme.nix files.