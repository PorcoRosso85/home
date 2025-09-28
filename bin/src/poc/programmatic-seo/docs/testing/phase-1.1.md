# Phase 1.1 Verification Document

**Phase**: 1.1 - Lite+pSEO（静的サイトマップ＆hreflang 生成）
**Purpose**: Zero-Cloudflare static sitemap.xml and hreflang generation for pSEO activation
**Created**: 2024-09-28
**Status**: Verification procedures for final acceptance

## Overview

Phase 1.1 implements build-time generation of `sitemap.xml` and `hreflang` tags to provide pSEO activation points while maintaining zero Cloudflare dependencies.

## Implementation Components

### Core Scripts
- `scripts/build-sitemap.ts` - Static URL list → sitemap.xml generation
- `scripts/build-hreflang.ts` - URL language mapping → hreflang link tags
- `packages/i18n/locales.ts` - Language definitions and defaults
- `packages/i18n/meta.ts` - Title/description generation helpers

### Generated Outputs
- `public/sitemap.xml` - XML sitemap with valid URLs and lastmod
- `public/hreflang.html` - HTML hreflang link tags for manual verification
- Language-specific URL mappings with x-default fallback

## Verification Procedures

### 1. Sitemap.xml Generation

#### Command
```bash
nix run .#build-sitemap
```

#### Expected Outputs
- `public/sitemap.xml` created or updated
- Valid XML structure conforming to sitemap.xml standard
- URL count > 0 (not empty)
- Valid `<loc>` and `<lastmod>` entries
- XML Sitemaps Validator compatible structure

#### Validation Steps
```bash
# 1. Generate sitemap
nix run .#build-sitemap

# 2. Verify file exists and has content
ls -la public/sitemap.xml
wc -l public/sitemap.xml

# 3. Check XML structure validity
# Manual inspection: ensure proper XML format, urlset namespace, loc/lastmod tags

# 4. Verify URL count and content
grep -c "<url>" public/sitemap.xml
grep "<loc>" public/sitemap.xml | head -3
grep "<lastmod>" public/sitemap.xml | head -3
```

#### Success Criteria
- [ ] `public/sitemap.xml` exists after build
- [ ] File contains valid XML with `<urlset>` root
- [ ] Contains `<url>` entries with valid `<loc>` and `<lastmod>`
- [ ] URL count > 0 (sitemap not empty)
- [ ] lastmod dates are in ISO 8601 format

### 2. Hreflang Link Generation

#### Command
```bash
nix run .#build-hreflang
```

#### Expected Outputs
- Hreflang link tags generated for major pages
- Cross-referential links between language variants
- `x-default` hreflang included for fallback
- Output formatted for HTML `<head>` insertion

#### Validation Steps
```bash
# 1. Generate hreflang links
nix run .#build-hreflang

# 2. Check output files
ls -la public/hreflang.*

# 3. Verify hreflang structure
cat public/hreflang.html | grep -E 'hreflang="(en|ja|x-default)"'

# 4. Test integration with example page
open examples/phase-1.0/json-ld-test.html
# Manual browser check: inspect <head> for hreflang link tags
```

#### Success Criteria
- [ ] Hreflang output files generated in `public/`
- [ ] Contains mutual cross-references between language variants
- [ ] Includes `x-default` hreflang for fallback
- [ ] Link tags properly formatted for HTML `<head>` insertion
- [ ] Covers major pages defined in URL source data

### 3. Browser Verification

#### Manual Testing with json-ld-test.html

The `examples/phase-1.0/json-ld-test.html` file serves as the primary test page for hreflang verification.

#### Steps
```bash
# 1. Start local server
nix run .#serve-examples

# 2. Open test page
# Navigate to: http://localhost:8080/examples/phase-1.0/json-ld-test.html

# 3. Browser inspection
# - Open Developer Tools (F12)
# - Inspect <head> section
# - Verify hreflang <link> tags are present
# - Check for proper lang codes (en, ja, x-default)
# - Validate href URLs are correctly formatted
```

#### Browser Verification Checklist
- [ ] Page loads without JavaScript errors
- [ ] `<head>` contains hreflang `<link rel="alternate">` tags
- [ ] Multiple language variants visible (en, ja, x-default)
- [ ] URLs in hreflang tags are properly formatted
- [ ] No broken or malformed link elements

### 4. Comprehensive System Validation

#### All Checks Command
```bash
nix flake check
```

This executes all validation checks defined in `flake.nix`:
- `tscheck` - TypeScript type safety
- `build` - Snippet build verification
- `sitemap-exists` - Sitemap file presence
- `sitemap-validation` - Sitemap content validation
- `hreflang-validation` - Hreflang structure validation
- `phase-guard` - Phase guard compliance

#### Success Criteria
- [ ] All `nix flake check` tests pass
- [ ] No TypeScript compilation errors
- [ ] Build artifacts generated successfully
- [ ] Phase guard validations complete
- [ ] No validation script failures

### 5. XML Sitemaps Validator Compatibility

#### Structure Requirements
The generated `sitemap.xml` must conform to XML Sitemaps protocol for validator compatibility:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/page</loc>
    <lastmod>2024-09-28T10:00:00Z</lastmod>
  </url>
</urlset>
```

#### Compatibility Checklist
- [ ] Proper XML declaration with UTF-8 encoding
- [ ] Standard sitemap namespace declaration
- [ ] Valid `<url>`, `<loc>`, `<lastmod>` structure
- [ ] ISO 8601 formatted timestamps
- [ ] No invalid characters or encoding issues

## Implementation Verification Log

### Generated Files Status
```bash
# After running build commands, verify:
ls -la public/sitemap.xml public/hreflang.*
```

### Command Execution Log
```bash
# Record of verification command execution:
echo "=== Sitemap Generation ==="
nix run .#build-sitemap
echo "Exit code: $?"

echo "=== Hreflang Generation ==="
nix run .#build-hreflang
echo "Exit code: $?"

echo "=== Comprehensive Validation ==="
nix flake check
echo "Exit code: $?"
```

### Content Validation Results
```bash
# Sitemap content summary:
echo "Sitemap URL count: $(grep -c "<url>" public/sitemap.xml)"
echo "Sample URLs:"
grep "<loc>" public/sitemap.xml | head -3

# Hreflang link summary:
echo "Hreflang link count: $(grep -c 'hreflang=' public/hreflang.html)"
echo "Languages detected:"
grep -o 'hreflang="[^"]*"' public/hreflang.html | sort | uniq
```

## Final Acceptance Criteria

### DoD (Definition of Done) Verification

#### ✅ Automatic Verification (Required)
- [ ] `nix run .#build-sitemap` → `public/sitemap.xml` generated (URL count > 0, valid loc/lastmod)
- [ ] `nix run .#build-hreflang` → major pages have cross-referential hreflang links (x-default included)
- [ ] `nix flake check` → all validation gates pass (type/build/exist/phase-guard checks)
- [ ] XML Sitemaps Validator compatible structure confirmed

#### ✅ Manual Verification (Required)
- [ ] Browser test with `examples/phase-1.0/json-ld-test.html` shows hreflang links in `<head>`
- [ ] No JavaScript errors in browser console during manual testing
- [ ] Generated URLs are accessible and properly formatted

### Phase Completion Gates

#### ✅ File Creation Requirements
- [ ] `docs/.receipts/1.1.done` exists with commit-hash/approved-by/gates info
- [ ] `docs/PHASES_STATUS.json` updated (Phase 1.1 → completed)
- [ ] `docs/phases/1.1-Lite-pSEO.md` deleted (phase guard enforcement)

#### ✅ Quality Assurance
- [ ] All implementation checklist items validated
- [ ] No regressions in existing Phase 1.0 functionality
- [ ] Generated artifacts ready for production deployment
- [ ] Rollback procedures documented and tested

## Notes

- URL source is currently CSV/JSON-based for Phase 1.1, with D1 migration planned for Phase 1.2
- This verification document serves as primary procedure for Phase 1.1 final acceptance
- All verification steps must pass before phase completion processing
- Generated files should be production-ready for static site deployment

## Verification Completion

**Date**: ___________
**Verifier**: ___________
**Status**: ☐ PASSED ☐ FAILED
**Next Steps**: Phase completion processing or issue resolution
