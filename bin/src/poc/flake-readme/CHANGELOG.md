# Changelog

All notable changes to the flake-readme project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - Major Version (SemVer MAJOR)

### BREAKING CHANGES
- **BREAKING CHANGE: Ignore-Only Policy Transition (Fact-Policy Separation)**: Complete architectural change from mixed fact-policy logic to Single Responsibility Principle separation
  - **Policy Change**: Missing detection no longer uses `.nix-only documentable detection` logic
  - **Impact**: All directories (except explicitly ignored) now require `readme.nix` files
  - **Architecture**: `isDocumentable` function preserved as fact collection only, removed from missing detection logic
  - **SemVer Treatment**: MAJOR version bump required due to breaking behavioral changes
  - **Migration Paths**:
    - **Temporary exclusions**: Use `ignoreExtra = [ "dir1" "dir2" ]` configuration
    - **Permanent exclusions**: Use `git rm -r --cached unwanted-dir/` then `.gitignore`
  - **Timeline**: Effective immediately - all non-.nix directories now subject to documentation requirements
  - **API Preservation**: `isDocumentable` function remains available for fact collection and future extensibility
  - **Benefits**: Clear separation between system facts (what exists) and policy decisions (what requires documentation)

### Removed
- **Legacy Test Files**: Removed `test-nix-only-*.nix` and `test-documentable-nix-only.nix` files
  - **Replacement**: New unified `test-ignore-only-comprehensive.nix` covers all representative cases
  - **Coverage**: 4 key scenarios (non-.nix/has-.nix/ignore/root) maintained in single test
- **Backup Files**: Cleaned up `readme.nix.bak-*` backup files from development
- **Legacy Documentation**: Moved outdated specifications to `DEPRECATED_SPECS/` directory
- **Removed .no-readme Marker Support**: The `.no-readme` marker file functionality has been completely removed to simplify the codebase
  - **Migration Required**: Directories using `.no-readme` markers must migrate to alternative approaches:
    - **Option 1**: Add directories to `.gitignore` to exclude them from documentation processing
    - **Option 2**: Use `ignoreExtra` configuration option in flake-parts integration
  - **Simplification Benefits**: 
    - Reduced complexity in documentable directory detection (~43 lines removed)
    - Cleaner core logic focused on `.nix` file presence only
    - Better alignment with standard Nix ecosystem patterns
  - **Impact**: Existing projects with `.no-readme` files will now have those directories processed for documentation
  - **Timeline**: Remove `.no-readme` files and implement migration before next update

### Added
- **v1 Extension Field Warnings System**: v1 schema documents now generate warnings for unknown top-level fields while preserving backward compatibility
  - Unknown fields generate warning messages in format: `"Unknown keys found at .: [field1, field2, ...]"`
  - Extension fields are preserved in the `extra` field for inspection
  - Documents remain valid (warnings don't cause validation failures)
  - Supports experimentation with future schema features without breaking existing workflows

### Changed
- **Warning Behavior**: v1 documents with extension fields now properly generate warnings instead of silently dropping unknown fields
- **Field Preservation**: Unknown fields in v1 documents are now preserved for inspection rather than being silently removed

### Impact Notes

#### For New Users
- No impact - follow the v1 schema specification as documented
- Extension fields will generate helpful warnings if accidentally added

#### For Existing Users
- **Low Impact**: Most users following the v1 specification will see no changes
- **Extension Field Users**: If you have v1 documents with fields not in the official specification (like `usage`, `features`, `techStack`), you'll now see warnings
- **Warnings Don't Break Builds**: All warnings are informational - your validation will still pass

#### For strict=true Users
- **Potential Impact**: If using `strict = true` policy option, extension field warnings will now cause validation failures
- **Recommendation**: Review any extension fields and either:
  - Move them to the `meta` field (recommended): `meta = { usage = ".."; features = [...]; };`
  - Remove them if not needed
  - Set `strict = false` if you want to keep warnings without failures

### Migration Guide

If you receive new v1 extension field warnings:

1. **Identify Extension Fields**: Look for fields not in the allowed list: `description`, `goal`, `nonGoal`, `meta`, `output`, `source`

2. **Choose Migration Strategy**:
   ```nix
   # Before (generates warnings)
   {
     description = "My project";
     goal = [ "..." ];
     nonGoal = [ "..." ];
     meta = { lifecycle = "stable"; };
     output = { packages = []; };
     
     # Extension fields (warning sources)
     usage = "Advanced examples";
     features = [ "feature-a" ];
     techStack = { language = "nix"; };
   }
   
   # After (recommended approach)
   {
     description = "My project";  
     goal = [ "..." ];
     nonGoal = [ "..." ];
     meta = { 
       lifecycle = "stable";
       # Move extension fields here
       usage = "Advanced examples";
       features = [ "feature-a" ];
       techStack = { language = "nix"; };
     };
     output = { packages = []; };
   }
   ```

3. **Verify**: Run `nix flake check` to confirm warnings are resolved

### Technical Details
- Extension field detection is performed during v1 schema validation
- Warning generation preserves document validity
- Field preservation enables gradual migration and future schema evolution
- Implementation maintains backward compatibility with existing tooling