# API Behavior Verification Guide

This guide covers manual verification of all measurement snippet APIs for Phase 1.0.

## Prerequisites

1. Start the local server: `nix run .#serve-examples`
2. Open browser to: http://localhost:8080/examples/phase-1.0/
3. Open browser developer tools (F12)

## Verification Checklist

### ✅ Step 5a: Basic Functionality

**Test Page: http://localhost:8080/examples/phase-1.0/**

1. **Page Loading**
   - [ ] Page loads without JavaScript errors
   - [ ] "IIFE snippet loaded successfully ✓" message appears
   - [ ] No CSP violations in console

2. **Provider Detection**
   - [ ] Mock providers show as available: `gtag=true, plausible=true`
   - [ ] Console shows mock provider calls

3. **Manual API Testing**
   - [ ] Click "Track Pageview" button → See "Pageview tracked ✓"
   - [ ] Click "Track Custom Click" button → See "Custom click tracked ✓"
   - [ ] Click "Decorate Outbound Links" → See "Outbound links decorated ✓"

### ✅ Step 5b: CSP Compliance

**Test Page: http://localhost:8080/examples/phase-1.0/csp-test.html**

1. **CSP Environment**
   - [ ] Page loads with strict CSP header
   - [ ] External IIFE script loads successfully
   - [ ] No CSP violations for measurement snippet

2. **Provider Integration**
   - [ ] Mock providers work with nonce-secured scripts
   - [ ] API functions work in CSP environment

### ✅ Step 5c: Comprehensive API Testing

**Browser Console Testing:**

1. Load the API test suite:
   ```javascript
   // Copy-paste api-test.js content into console, then run:
   runAPITests()
   ```

2. **Expected Test Results:**
   - [ ] All initialization tests pass
   - [ ] Pageview idempotency works (duplicates prevented)
   - [ ] Click tracking handles outbound/internal links correctly
   - [ ] Click idempotency works (duplicates prevented)
   - [ ] Outbound link decoration completes without errors
   - [ ] No-op safety works when providers unavailable
   - [ ] SSR safety simulation passes
   - [ ] State management handles multiple initializations

3. **Target Success Rate:** ≥90% (allow for environment-specific issues)

### ✅ Step 5d: SSR Safety

**Simulated SSR Testing:**

1. **Window Undefined Simulation:**
   ```javascript
   // In console, test defensive coding:
   const originalWindow = window;
   window = undefined;

   // These should not throw errors:
   pSEO.init({ provider: 'ga4', siteId: 'test' });
   pSEO.trackPageview();
   pSEO.trackClick(null);

   // Restore window
   window = originalWindow;
   ```

2. **Expected Behavior:**
   - [ ] No JavaScript errors thrown
   - [ ] Functions become no-ops safely
   - [ ] Global state remains consistent

### ✅ Step 5e: Idempotency Testing

**Manual Duplicate Prevention:**

1. **Pageview Idempotency:**
   ```javascript
   // Clear mock events
   window.mockGtagEvents = [];

   // Track multiple pageviews rapidly
   pSEO.trackPageview();
   pSEO.trackPageview();
   pSEO.trackPageview();

   // Check events array - should have only 1 config event
   console.log(window.mockGtagEvents);
   ```

2. **Click Idempotency:**
   ```javascript
   // Create test element
   const testLink = document.createElement('a');
   testLink.href = 'https://test.example.com';
   testLink.textContent = 'Test Link';

   // Clear events and track rapidly
   window.mockGtagEvents = [];
   pSEO.trackClick(testLink, { action: 'test-click' });
   pSEO.trackClick(testLink, { action: 'test-click' }); // Duplicate

   // Should have only 1 event
   console.log(window.mockGtagEvents.filter(e => e.action === 'test-click'));
   ```

3. **Expected Results:**
   - [ ] Duplicate pageviews prevented (1 second threshold)
   - [ ] Duplicate clicks prevented (1 second threshold)
   - [ ] Event arrays contain expected number of events

### ✅ Step 5f: Outbound Link Detection

**Link Classification Testing:**

1. **Test Links (on main page):**
   - https://github.com → Should be detected as outbound
   - https://google.com → Should be detected as outbound
   - /internal → Should be detected as internal
   - #internal → Should be detected as internal

2. **Manual Verification:**
   ```javascript
   // Test detection logic
   const testUrls = [
     'https://github.com',
     'https://google.com',
     '/internal-page',
     '#section',
     'mailto:test@example.com'
   ];

   testUrls.forEach(url => {
     const link = document.createElement('a');
     link.href = url;
     console.log(`${url}: ${isOutboundLink(url) ? 'OUTBOUND' : 'INTERNAL'}`);
   });
   ```

3. **Expected Classification:**
   - [ ] External domains → outbound
   - [ ] Same domain → internal
   - [ ] Relative paths → internal
   - [ ] Hash links → internal
   - [ ] Protocol links (mailto:, tel:) → outbound

## Success Criteria

### Phase 1.0 API Verification Complete When:

1. **✅ All Basic Tests Pass**
   - Page loading works
   - Provider detection works
   - Manual buttons work

2. **✅ CSP Compliance Verified**
   - External IIFE loads under strict CSP
   - No CSP violations
   - Nonce-secured initialization works

3. **✅ Comprehensive Test Suite Passes**
   - ≥90% success rate on automated tests
   - No critical functionality failures

4. **✅ Safety Features Verified**
   - SSR safety (no window errors)
   - No-op safety (missing providers)
   - Idempotency (duplicate prevention)

5. **✅ Link Detection Accurate**
   - Outbound links correctly identified
   - Internal links correctly identified
   - Edge cases handled properly

## Troubleshooting

### Common Issues

**"pSEO is not defined"**
- Verify IIFE script loaded: Check Network tab
- Check for 404 errors on snippet.iife.js
- Verify server is running on correct port

**"Provider not detected"**
- Check mock provider setup in page source
- Verify no JavaScript errors preventing provider init
- Confirm provider scripts load before measurement snippet

**CSP Violations**
- Check CSP header configuration
- Verify nonce matches between header and script tags
- Ensure external script domain is allowed

**API Tests Failing**
- Check browser console for specific error messages
- Verify test environment matches expected conditions
- Try refreshing page and re-running tests

## Manual Verification Log

Document your verification results:

```
Phase 1.0 API Verification - [DATE]

Basic Functionality: [ PASS / FAIL ]
CSP Compliance: [ PASS / FAIL ]
Comprehensive Tests: [ X/Y PASSED ] [ SUCCESS_RATE% ]
SSR Safety: [ PASS / FAIL ]
Idempotency: [ PASS / FAIL ]
Link Detection: [ PASS / FAIL ]

Notes: [Any specific observations or issues]

Verified by: [Name]
Environment: [Browser/Version/OS]
```