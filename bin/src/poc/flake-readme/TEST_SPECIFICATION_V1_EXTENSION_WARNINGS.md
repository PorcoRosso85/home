# Test Specification: v1 Extension Field Warnings

## Context
Bug fix for flake-readme system where v1 schema documents with extension fields (like `usage`, `features`, `techStack`) are silently ignored instead of generating warnings.

## Current Behavior (RED Phase - ❌ FAILING)
- v1 documents with extension fields are processed normally
- Extension fields are silently dropped during normalization  
- No warnings are generated (`warningCount: 0`, `warnings: []`)
- Fields like `usage`, `features`, `techStack` completely disappear from the output

## Expected Behavior (GREEN Phase - Target)
- v1 documents should preserve extension fields and generate warnings
- Warning message format: `"Unknown keys found at .: [usage, features, techStack]"`
- `warningCount > 0` indicating validation issues
- Extension fields should be stored in an `extra` field for inspection

## Test Implementation

### Test File Location
- **Primary test**: `/home/nixos/bin/src/poc/flake-readme/flake.nix` (checks.v1-extension-warnings)  
- **Example file**: `/home/nixos/bin/src/poc/flake-readme/examples/invalid/v1-extension-fields.nix`

### Test Document Structure
```nix
{
  # Valid v1 schema fields
  description = "Test v1 document with extension fields";
  goal = [ "test extension field warnings" ];
  nonGoal = [ "being a standard v1 document" ];
  meta = { test = "v1-extensions"; };
  output = { packages = [ "test-package" ]; };
  
  # Extension fields that should generate warnings
  usage = "This should trigger a warning";
  features = [ "feature1" "feature2" ];
  techStack = { language = "nix"; framework = "flake-parts"; };
}
```

### Test Validation Points
1. **Warning Count**: `warningCount > 0` (currently fails with `warningCount: 0`)
2. **Warning Message**: Contains `"Unknown keys found"` pattern
3. **Extension Fields**: All three fields (`usage`, `features`, `techStack`) mentioned in warnings
4. **Document Validity**: Document should remain valid with warnings, not errors

### Current Test Output (RED Phase)
```bash
❌ Expected warnings for v1 extension fields but found none
This indicates that v1 documents with extension fields are not generating warnings
Extension fields like 'usage', 'features', 'techStack' should trigger warnings in v1 schema
```

### Test Command
```bash
nix build .#checks.x86_64-linux.v1-extension-warnings -L
```

## Root Cause Analysis
Looking at `lib/core-docs.nix`:

1. **Line 84**: `isV1` detection only checks for `description`, `goal`, `nonGoal`
2. **Lines 87-99**: v1 normalization explicitly filters to known fields only:
   - `description`, `goal`, `nonGoal`, `meta`, `output`, `source`
3. **Extension fields are silently dropped** - they never reach the validation logic
4. **Lines 210-212**: Warning logic for `extra` fields only applies to legacy documents

## Implementation Strategy (Next Steps)
1. **Modify `normalizeDoc`**: Preserve extension fields in v1 documents (similar to legacy handling)
2. **Add v1 extension field warnings**: Check for unknown keys in v1 schema validation
3. **Update warning message**: Ensure consistent format across schema versions
4. **Verify test passes**: Confirm GREEN phase after implementation

## Success Criteria
- Test passes with `exit 0`
- `warningCount > 0` in test output
- Warning message includes all extension fields
- v1 documents with extension fields generate warnings but remain processable