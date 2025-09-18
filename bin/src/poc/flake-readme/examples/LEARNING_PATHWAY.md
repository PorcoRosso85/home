# Learning Pathway: From Valid to Invalid Examples

This document maps the learning progression from valid readme.nix examples to common error cases, helping developers understand the validation system step by step.

## Learning Progression

### 1. Valid Examples (✅ Baseline)
Start with these working examples to understand proper structure:

| Example | Purpose | Key Learning |
|---------|---------|--------------|
| [`application/readme.nix`](./application/readme.nix) | Clean v1 schema | Proper field structure, complete output specification |
| [`domain/readme.nix`](./domain/readme.nix) | Business logic documentation | Clear goal/nonGoal separation, lifecycle metadata |
| [`flake-parts-integration/readme.nix`](./flake-parts-integration/readme.nix) | Integration pattern | Minimal setup, flake-parts compatibility |

### 2. Warning Cases (⚠️ Non-blocking)
Learn about warnings that don't prevent validation:

| Example | Warning Type | Learning Focus |
|---------|--------------|----------------|
| [`invalid/v1-extension-fields.nix`](./invalid/v1-extension-fields.nix) | Extension fields | Understanding v1 schema boundaries, field preservation |

### 3. Error Cases (❌ Blocking)
Understand validation failures and how to fix them:

| Example | Error Type | Learning Focus |
|---------|------------|----------------|
| [`invalid/empty-goal.nix`](./invalid/empty-goal.nix) | Empty required field | Why goals must be non-empty arrays |
| [`invalid/empty-nongoal.nix`](./invalid/empty-nongoal.nix) | Empty required field | Why nonGoals must be specified |
| [`invalid/invalid-goal-type.nix`](./invalid/invalid-goal-type.nix) | Type validation | Array vs string requirements |
| [`invalid/missing-description.nix`](./invalid/missing-description.nix) | Missing required field | Essential schema fields |
| [`invalid/unknown-output-keys.nix`](./invalid/unknown-output-keys.nix) | Invalid output schema | Output field restrictions |

## Progressive Learning Path

### Phase 1: Understanding Valid Structure
1. **Read** [`application/readme.nix`](./application/readme.nix) - See a complete, valid example
2. **Compare** with [`domain/readme.nix`](./domain/readme.nix) - Notice consistent patterns
3. **Examine** [`flake-parts-integration/readme.nix`](./flake-parts-integration/readme.nix) - Minimal valid setup

**Key Takeaways:**
- All examples have: `description`, `goal`, `nonGoal`, `meta`, `output`
- Goals and nonGoals are always arrays of strings
- Meta and output allow structured data
- Different projects use similar patterns

### Phase 2: Understanding Warnings vs Errors
4. **Study** [`invalid/v1-extension-fields.nix`](./invalid/v1-extension-fields.nix) ⭐ **FEATURED EXAMPLE**
   
**Key Learning:**
- Extension fields generate warnings but don't fail validation
- Unknown fields like `usage`, `features`, `techStack` are preserved
- Warnings help identify potential issues without blocking development
- Multiple resolution strategies available (ignore, move to meta, remove, or wait for schema updates)

### Phase 3: Fixing Common Errors  
5. **Learn from** [`invalid/empty-goal.nix`](./invalid/empty-goal.nix) - Empty arrays fail validation
6. **Understand** [`invalid/invalid-goal-type.nix`](./invalid/invalid-goal-type.nix) - Type requirements
7. **Fix** other validation errors using the pattern

**Key Learning:**
- Hard errors prevent validation success
- Type validation is strict (arrays vs strings)
- Empty required fields always fail
- Error messages point to specific problems

## Validation Commands

Test your understanding by running validation on different examples:

```bash
# ✅ These should pass
nix run .#readme-check  # Validates all examples in the project

# ⚠️  This generates warnings but passes
cd examples/invalid && cat v1-extension-fields.nix  # Study the comprehensive comments

# ❌ These should fail (use for learning error messages)
# Note: Individual file validation not supported yet, use nix flake check for testing
```

## Pattern Recognition

After working through these examples, you should recognize:

1. **Valid Pattern**:
   ```nix
   {
     description = "Clear project description";
     goal = [ "actionable goal" ];
     nonGoal = [ "what this doesn't do" ];
     meta = { /* structured metadata */ };
     output = { /* defined output keys only */ };
   }
   ```

2. **Warning Pattern** (v1 extension fields):
   ```nix
   {
     # ... valid v1 fields ...
     customField = "triggers warning";  # Preserved but warned
   }
   ```

3. **Error Patterns**:
   ```nix
   {
     # ❌ Missing required field
     goal = [ "something" ];  # Missing description
     
     # ❌ Wrong type  
     goal = "string instead of array";
     
     # ❌ Empty required field
     goal = [ ];  # Empty array fails
   }
   ```

## Next Steps

Once you understand these patterns:
1. Create your own readme.nix following the valid examples
2. Run validation and learn from any errors
3. Use the invalid examples to troubleshoot issues
4. Contribute improvements to these educational materials!

## Questions or Issues?

- Review the [Invalid Examples README](./invalid/README.md) for detailed explanations
- Check the [Schema Reference](../docs/schema.md) for complete specifications
- Study the comprehensive comments in each example file