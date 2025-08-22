# Golden Master Test for Corporate List Scraper

This directory contains golden master tests to protect the current behavior of the corporate list scraper during TypeScript migration.

## Overview

The golden master test captures the current behavior of `scrape.mjs` and validates that future changes maintain compatibility. This is essential during the TypeScript migration to ensure no functionality is lost.

## Files

- `golden-master.test.js` - Main test suite that compares new runs against the golden standard
- `fixtures/golden.json` - Captured baseline data from a successful scraper run (120 articles)
- `validate-golden.js` - Quick validation script to verify test setup without running the scraper
- `README.md` - This documentation

## Running Tests

### Quick Validation (Recommended First)
```bash
# Validate the golden master setup without running scraper
npm run test:validate
```

### Full Golden Master Test
```bash
# Run complete golden master test (takes 2-3 minutes)
npm run test:golden
```

### Standard Test Runner
```bash
# Run all tests
npm test
```

## What the Tests Protect

### 1. Data Structure Consistency
- All articles have required fields: `source`, `company_name`, `title`, `url`, `scraped_at`
- Field types and formats remain consistent
- JSON structure is maintained

### 2. Article Count Stability
- Expects ~120 articles total (3 keywords × ~40 articles each)
- Allows ±20 articles tolerance for normal variation
- Validates keyword coverage is maintained

### 3. Data Quality
- All URLs are valid PR TIMES links
- Titles are non-empty and reasonable length
- Timestamps are valid ISO format
- Source field is consistently "PR_TIMES"

### 4. Business Logic
- Company name extraction (currently ~0% success rate, which is expected)
- Keyword search functionality (シリーズA, 資金調達, 事業提携)
- Article deduplication and filtering

## Test Results Interpretation

### ✅ Passing Tests
- Structure matches golden master
- Article count within acceptable range
- All data quality checks pass
- No regressions detected

### ⚠️ Warning Conditions
- Minor article count variations (within ±20)
- Small changes in company name extraction rate
- Individual article differences (URLs/titles may change daily)

### ❌ Failing Conditions
- Major structure changes (missing fields, wrong types)
- Significant drop in article count (>20 articles)
- Complete failure of scraping functionality
- Invalid URLs or corrupted data

## Updating the Golden Master

If intentional changes are made that should update the baseline:

1. Verify the changes are intentional and correct
2. Run the scraper to generate new output:
   ```bash
   npm run scrape > test/fixtures/new-golden.json
   ```
3. Extract just the JSON array:
   ```bash
   grep -A 1000 '^\[' test/fixtures/new-golden.json | grep -B 1000 '^]$' > test/fixtures/golden.json
   ```
4. Validate the new golden master:
   ```bash
   npm run test:validate
   ```
5. Run the full test suite to ensure it passes:
   ```bash
   npm run test:golden
   ```

## Integration with CI/CD

These tests are designed to:
- Run in automated environments (CI/CD)
- Provide clear pass/fail status
- Generate detailed error reports for failures
- Complete within reasonable time limits (3-5 minutes)

## TypeScript Migration Support

During the TypeScript migration:
1. Run tests before any changes to establish baseline
2. Run tests after each major change to detect regressions
3. Use test failures as early warning of breaking changes
4. Update golden master only when behavior changes are intentional

## Troubleshooting

### Test Timeout
- Increase timeout in test file if network is slow
- Check that chromium is available in Nix shell
- Verify PR TIMES website is accessible

### Structure Mismatch
- Check if scraping logic was modified
- Verify field names and types match expectations
- Look for changes in article extraction patterns

### Count Variations
- Some variation is normal due to live data
- Large variations may indicate scraping issues
- Check if search keywords are still working

## Notes

- Tests use live data from PR TIMES, so some variation is expected
- Golden master was captured on: 2025-08-22 18:58:19 UTC
- Company name extraction currently returns mostly null values (0% success rate)
- This is the expected behavior and not a test failure