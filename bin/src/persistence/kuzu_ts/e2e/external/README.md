# External E2E Test - Version Management

This directory contains end-to-end tests that verify `kuzu_ts` can be used as an external package from other projects.

## Version Management Approach

### Accessing the KuzuDB Version

The `kuzu_ts` module exports `KUZU_VERSION` which provides the version of the underlying KuzuDB library. External projects can use this for:

1. **Compatibility Checks**: Ensure the KuzuDB version meets minimum requirements
2. **Dependency Management**: Track which version of KuzuDB is being used
3. **Feature Detection**: Determine available features based on version
4. **Debugging**: Log version information for troubleshooting

### Example Usage

```typescript
import { KUZU_VERSION, createDatabase } from "kuzu_ts";

// Log the version
console.log(`Using KuzuDB version: ${KUZU_VERSION}`);

// Check compatibility
const [major, minor, patch] = KUZU_VERSION.split('.').map(Number);
if (major < 1 || (major === 1 && minor < 0)) {
  throw new Error(`KuzuDB version ${KUZU_VERSION} is too old. Please upgrade to 1.0.0 or later.`);
}

// Feature detection example
const supportsFeatureX = major > 1 || (major === 1 && minor >= 2);
if (supportsFeatureX) {
  // Use new feature
}
```

### Version Synchronization

The `KUZU_VERSION` exported by `kuzu_ts` is defined in `version.ts` and should match the version of the `npm:kuzu` package used internally. This ensures:

- Version consistency across the wrapper and native library
- Clear communication about which KuzuDB version is in use
- Ability to track version changes over time

### Flake Integration

While the current flake.nix uses a fixed version of `npm:kuzu@0.10.0`, future implementations could:

1. Read the version from the `kuzu_ts` module dynamically
2. Ensure the npm package version matches `KUZU_VERSION`
3. Provide version overrides for testing different versions

Example of potential dynamic version usage in flake.nix:
```nix
# Future enhancement: dynamically determine version
# This would require evaluating the TypeScript module
# to extract KUZU_VERSION at build time
${pkgs.deno}/bin/deno install --allow-scripts=npm:kuzu@${kuzu-version}
```

### Testing Version Management

The test file `test_e2e_import.ts` includes comprehensive version testing:

- Verifies `KUZU_VERSION` is exported and accessible
- Validates the version format (semantic versioning)
- Demonstrates compatibility checking patterns
- Shows how to parse and use version components

Run the tests with:
```bash
nix run .#test
```

## Best Practices for External Projects

1. **Always check version compatibility** at startup
2. **Log the KuzuDB version** for debugging purposes
3. **Handle version mismatches gracefully** with clear error messages
4. **Document minimum required versions** in your project
5. **Consider version-specific feature flags** for optional functionality