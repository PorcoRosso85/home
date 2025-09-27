# Phase 1.0 Testing Documentation

Complete verification procedures for Programmatic SEO Phase 1.0 implementation.

## Overview

Phase 1.0 implements a zero-Cloudflare foundation with measurement snippets and JSON-LD generators. This document provides step-by-step verification procedures.

## Prerequisites

1. Development environment: `nix develop`
2. Local server running: `nix run .#serve-examples`
3. All build artifacts generated: `nix run .#build-snippet`

## Step-by-Step Verification

### ✅ Gate 1: Type Safety (Step 2)

**Command:** `nix run .#check`

**Expected Result:**
```
Running TypeScript type check...
Type check passed - no errors found
```

**Success Criteria:**
- [ ] Zero TypeScript compilation errors
- [ ] All packages/* modules type-check successfully
- [ ] Strict type checking enabled

### ✅ Gate 2: Build Verification (Step 3)

**Command:** `nix run .#build-snippet`

**Expected Results:**
```
Build completed:
  dist/measurement/snippet.esm.js (5530 bytes)
  dist/measurement/snippet.iife.js (3481 bytes)
```

**Success Criteria:**
- [ ] Both ESM and IIFE artifacts generated
- [ ] File sizes reasonable (3-6KB range)
- [ ] No build errors or warnings
- [ ] IIFE contains `pSEO` global variable
- [ ] ESM contains proper exports

### ✅ Browser Integration Testing (Step 4)

**Test Page:** http://localhost:8080/examples/phase-1.0/

**Verification Steps:**
1. Open test page in browser
2. Check developer console for errors
3. Verify "IIFE snippet loaded successfully ✓" message
4. Test manual API buttons:
   - [ ] "Track Pageview" → "Pageview tracked ✓"
   - [ ] "Track Custom Click" → "Custom click tracked ✓"
   - [ ] "Decorate Outbound Links" → "Outbound links decorated ✓"

**Success Criteria:**
- [ ] Page loads without JavaScript errors
- [ ] All manual API tests pass
- [ ] Mock provider detection works
- [ ] Console shows measurement events

### ✅ CSP/Nonce Testing (Step 4.5)

**Test Page:** http://localhost:8080/examples/phase-1.0/csp-test.html

**Verification Steps:**
1. Open CSP test page
2. Check for CSP violations in console (should be none)
3. Verify external IIFE script loads
4. Test provider integration with nonce-secured scripts
5. Verify API functionality under CSP restrictions

**Success Criteria:**
- [ ] No CSP violations in browser console
- [ ] External IIFE script loads successfully under strict CSP
- [ ] Mock providers work with nonce-secured initialization
- [ ] All API functions work in CSP environment

### ✅ API Behavior Verification (Step 5)

**Test Script:** http://localhost:8080/examples/phase-1.0/api-test.js

**Verification Steps:**
1. Open main test page: http://localhost:8080/examples/phase-1.0/
2. Open browser developer console
3. Copy and paste api-test.js content into console
4. Run: `runAPITests()`
5. Review test results summary

**Expected Results:**
```
📊 Test Results Summary
Total Tests: 15+
✅ Passed: 14+
❌ Failed: 0-1
📈 Success Rate: 90%+
```

**Success Criteria:**
- [ ] ≥90% test success rate
- [ ] Initialization tests pass
- [ ] Pageview idempotency works
- [ ] Click idempotency works
- [ ] No-op safety verified (missing providers)
- [ ] SSR safety simulation passes
- [ ] Outbound link detection accurate

### ✅ JSON-LD Quality Verification (Step 6)

**Test Page:** http://localhost:8080/examples/phase-1.0/json-ld-test.html

**Verification Steps:**
1. Copy test page URL: `http://localhost:8080/examples/phase-1.0/json-ld-test.html`
2. Open [Google Rich Results Test](https://search.google.com/test/rich-results)
3. Paste URL and click "Test URL"
4. Wait for validation to complete
5. Take screenshots of results

**Expected Rich Results:**

**WebPage Schema:**
- ✅ Valid WebPage detected
- ✅ No warnings or errors
- ✅ Organization author recognized

**ImageObject Schema:**
- ✅ Valid ImageObject detected
- ✅ Eligible for image search features
- ✅ Proper dimensions and metadata

**ItemList Schema:**
- ✅ Valid ItemList detected
- ✅ All 4 list items recognized
- ✅ Proper positioning and URLs

**HowTo Schema (Recipe):**
- ✅ Valid Recipe detected
- ✅ Eligible for recipe rich snippets
- ✅ Ingredients and steps recognized
- ✅ Timing information valid (ISO 8601)

**HowTo Schema (Tutorial):**
- ✅ Valid HowTo detected
- ✅ Eligible for how-to rich snippets
- ✅ Tools and steps recognized
- ✅ Difficulty level recognized

**Success Criteria:**
- [ ] Zero warnings in Rich Results Test
- [ ] All 5 structured data types validated
- [ ] Eligible for relevant rich snippets
- [ ] Screenshots captured for documentation

### ✅ Additional Validation

**Schema.org Validator:** https://validator.schema.org/
- [ ] Paste URL and verify no schema errors

**JSON-LD Validator:** https://jsonld.com/validator/
- [ ] Extract JSON-LD and verify syntax

## Troubleshooting

### Common Issues

**TypeScript Errors:**
- Check tsconfig.json configuration
- Verify all packages/* imports are correct
- Ensure DOM types are available

**Build Failures:**
- Verify esbuild is available in nix environment
- Check for TypeScript errors first
- Confirm dist/ directory is writable

**Browser Loading Issues:**
- Ensure local server is running on port 8080
- Check network tab for 404s on snippet files
- Verify MIME types for .js files

**CSP Violations:**
- Check CSP header configuration
- Verify nonce matches between header and scripts
- Ensure external domains are allowed

**Rich Results Test Failures:**
- Verify server is publicly accessible OR use "Code" option
- Check JSON-LD syntax with validator
- Ensure all required properties are present

### Manual Verification Checklist

```
Phase 1.0 Verification - [DATE]

✅ Type Safety: [ PASS / FAIL ]
✅ Build Verification: [ PASS / FAIL ]
✅ Browser Integration: [ PASS / FAIL ]
✅ CSP/Nonce Testing: [ PASS / FAIL ]
✅ API Behavior: [ X/Y PASSED ] [ SUCCESS_RATE% ]
✅ JSON-LD Quality: [ PASS / FAIL ]
✅ Rich Results Screenshots: [ CAPTURED ]

Overall Status: [ PASS / FAIL ]

Notes: [Any specific observations]

Verified by: [Name]
Environment: [Browser/Version/OS]
Date: [YYYY-MM-DD]
```

## Success Criteria Summary

Phase 1.0 is considered **COMPLETE** when:

1. **✅ All Gates Passed**
   - Type safety (zero errors)
   - Build verification (artifacts generated)

2. **✅ All Browser Tests Pass**
   - Basic integration works
   - CSP compliance verified
   - API behavior verified (≥90% success)

3. **✅ JSON-LD Quality Verified**
   - Zero warnings in Rich Results Test
   - All structured data types valid
   - Screenshots captured

4. **✅ Documentation Complete**
   - All test procedures documented
   - Provider integration guide complete
   - Verification checklist completed

This establishes the foundation for Phase 1.2 integration with rwsdk-init and edge deployment.