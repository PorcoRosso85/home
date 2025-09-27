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

### 1-Line Integration (IIFE)
```html
<script src="./dist/measurement/snippet.iife.js"></script>
<script>
  pSEO.init({ provider: 'ga4', siteId: 'GA_MEASUREMENT_ID' });
  pSEO.decorateAllOutbound();
</script>
```

### ESM Integration
```javascript
import { init, decorateAllOutbound } from './dist/measurement/snippet.esm.js';

init({ provider: 'ga4', siteId: 'GA_MEASUREMENT_ID' });
decorateAllOutbound();
```

## Safety Features

- **SSR Safe**: No side effects in server environments (window guards)
- **Provider Delegation**: Uses official GA4/Plausible clients (no-op if unavailable)
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