# readme.nix Schema Reference

## v1 Schema (Current)

The complete v1 schema for readme.nix files:

```nix
{
  # Required core fields
  description = "One-line summary (≤80 chars)";
  goal = [ "What this component does" ];
  nonGoal = [ "What this component doesn't do" ];
  
  # Required metadata
  meta = {
    owner = [ "@team-or-person" ];
    lifecycle = "experimental"; # or "stable" | "deprecated"
  };
  
  # Required output declaration
  output = {
    packages = [ "package-name" ]; # Optional: list if any
    apps = [ "app-name" ]; # Optional: list if any
    modules = [ "module-name" ]; # Optional: list if any
    overlays = [ "overlay-name" ]; # Optional: list if any
    devShells = [ "shell-name" ]; # Optional: list if any
  };
}
```

## Field Definitions

### Core Fields

- **description**: Single-line project summary (max 80 characters)
- **goal**: Array of strings describing what this component does
- **nonGoal**: Array of strings describing what this component doesn't do

### Meta Fields

- **meta.owner**: Array of responsible teams/individuals (e.g., `["@team-name"]`)
- **meta.lifecycle**: Project stage (`"experimental"`, `"stable"`, or `"deprecated"`)

### Output Fields

The `output` object declares what this component provides:

- **packages**: List of package names this component exports
- **apps**: List of application names this component exports  
- **modules**: List of Nix module names this component exports
- **overlays**: List of overlay names this component exports
- **devShells**: List of development shell names this component exports

All output arrays can be empty (`[]`) if the component doesn't provide that type of output.

## Validation Rules

### Errors (will fail checks)

- Empty description
- Non-array goal or nonGoal
- Empty goal or nonGoal arrays
- Missing meta or output objects
- Non-object meta or output
- Non-string-array output fields

### Warnings (won't fail checks)

- Description exceeds 80 characters
- Unknown output keys (not in the allowed list above)
- Legacy schema usage
- **v1 extension fields**: Unknown top-level fields (not in the v1 specification)

## v1 Extension Field Warnings

The v1 schema supports exactly these top-level fields: `description`, `goal`, `nonGoal`, `meta`, `output`, and `source`. Any additional fields will generate warnings but won't cause validation failures.

### Allowed Top-Level Fields

- `description` - Required project summary
- `goal` - Required array of project goals
- `nonGoal` - Required array of what project doesn't do
- `meta` - Required metadata object
- `output` - Required output declaration object
- `source` - Optional source information

### Extension Field Behavior

When unknown fields are detected in v1 documents:

- **Warning Message**: `"Unknown keys found at .: [field1, field2, ...]"`
- **warningCount**: Increments for each unknown field type
- **Document Status**: Remains valid (warnings don't cause failures)
- **Field Preservation**: Extension fields are preserved in the `extra` field for inspection

### Example Extension Fields

```nix
{
  # Valid v1 fields
  description = "Example with extension fields";
  goal = [ "demonstrate warnings" ];
  nonGoal = [ "cause validation failures" ];
  meta = { lifecycle = "experimental"; };
  output = { packages = []; };
  
  # Extension fields (generate warnings)
  usage = "Advanced usage examples";        # ⚠️ Warning
  features = [ "feature-a" "feature-b" ];  # ⚠️ Warning  
  techStack = { language = "nix"; };       # ⚠️ Warning
}
```

### Handling Extension Field Warnings

When you encounter v1 extension field warnings, you have several options:

1. **Ignore warnings** (if experimenting with future schema features)
2. **Move data to meta field** (recommended approach):
   ```nix
   meta = {
     lifecycle = "experimental";
     usage = "Advanced usage examples";
     features = [ "feature-a" "feature-b" ];
     techStack = { language = "nix"; };
   };
   ```
3. **Remove extension fields** (cleanest v1 compliance)
4. **Wait for future schema** (that may officially support these fields)

## Policy Options

When using flake-parts integration, additional policy options are available:

- **strict**: Treat warnings as errors
- ~~**driftMode**~~: Removed in v2.0 (YAGNI principle) - Use static validation instead
- **failOnUnknownOutputKeys**: Fail when unknown output keys are found