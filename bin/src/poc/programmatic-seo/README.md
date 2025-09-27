# Programmatic SEO Phase 1.0

**Purpose**: Zero-Cloudflare "paste-only" foundation for programmatic SEO and lightweight measurement.

## Quick Start

```bash
# Development environment
nix develop

# Type check
nix run .#check

# Build snippets (ESM + IIFE)
nix run .#build-snippet

# Local testing server
nix run .#serve-examples
```

## Architecture

- **packages/measurement/** - Analytics snippet (GA4/Plausible delegation)
- **packages/seo/** - JSON-LD generators (ImageObject, Collection, HowTo)
- **public/** - Static assets (robots.txt, GSC verification)
- **examples/phase-1.0/** - Test pages for manual verification

## Integration

### Global API Options

The measurement snippet exposes two identical APIs:
- **`pSEO`** - Primary API (recommended for most use cases)
- **`window.MeasurementSnippet`** - Alternative API (for advanced scenarios with naming conflicts)

### 1-Line Integration (IIFE)
```html
<!-- Provider's official script (configured separately) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('config', 'GA_MEASUREMENT_ID');
</script>

<!-- Our measurement snippet (delegates to provider above) -->
<script src="./dist/measurement/snippet.iife.js"></script>
<script>
  // siteId should match the Measurement ID configured in the gtag script above
  pSEO.init({ provider: 'ga4', siteId: 'GA_MEASUREMENT_ID' });
  pSEO.decorateAllOutbound();
</script>
```

### ESM Integration
```javascript
// Ensure provider's official script is loaded separately (e.g., in HTML head)
// For GA4: gtag script with same GA_MEASUREMENT_ID
// For Plausible: plausible script with domain matching the siteId

import { init, decorateAllOutbound } from './dist/measurement/snippet.esm.js';

// siteId delegates to the provider's official implementation configured separately
init({ provider: 'ga4', siteId: 'GA_MEASUREMENT_ID' });
decorateAllOutbound();
```

## Safety Features

- **SSR Safe**: No side effects in server environments (window guards)
- **Provider Delegation**: Uses official GA4/Plausible clients (no-op if unavailable)
  - The measurement snippet does not directly use siteId for tracking
  - Instead, it delegates to the provider's official implementation (gtag for GA4, plausible for Plausible)
  - siteId should match the configuration in the provider's official script
- **Idempotent**: Duplicate click/pageview prevention
- **CSP Compatible**: External script distribution for strict CSP environments

## Verification

See `docs/testing/phase-1.0.md` for complete verification procedures including:
- TypeScript type safety
- Browser compatibility testing
- Rich Results Test validation
- Manual API testing scenarios

## Phase Scope

Phase 1.0 focuses on standalone operation with zero Cloudflare dependencies. Integration with rwsdk-init and edge deployment is planned for Phase 1.2.