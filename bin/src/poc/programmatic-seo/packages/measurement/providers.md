# Measurement Providers Setup Guide

## Provider Policy

### Delegation Strategy
Our measurement snippet follows a **delegation-first approach**:

- **GA4**: Delegates to official Google Analytics client (`window.gtag`). Does NOT use Measurement Protocol directly due to secret key requirements.
- **Plausible**: Delegates to official Plausible client (`window.plausible`).
- **No-op Safety**: If provider function is unavailable, tracking calls become no-op operations that never break the user interface.

### Architecture Benefits
- Zero vendor lock-in: Switch providers by changing configuration
- No API key management: Relies on official client libraries
- Resilient: Missing providers don't cause errors
- Lightweight: No bundled analytics libraries

## Setup Instructions

### 1. Basic Integration

Add the measurement snippet to your site:

```html
<!-- ESM Module (recommended for modern builds) -->
<script type="module">
  import { init, decorateAllOutbound } from './dist/measurement/snippet.esm.js';

  init({
    provider: 'ga4', // or 'plausible'
    siteId: 'GA_MEASUREMENT_ID', // Your tracking ID
    enableSPA: true, // Enable for single-page apps
  });

  // Auto-decorate outbound links
  decorateAllOutbound();
</script>
```

```html
<!-- IIFE Build (for simple script tag integration) -->
<script src="./dist/measurement/snippet.iife.min.js"></script>
<script>
  window.MeasurementSnippet.init({
    provider: 'ga4',
    siteId: 'GA_MEASUREMENT_ID',
    enableSPA: true,
  });

  window.MeasurementSnippet.decorateAllOutbound();
</script>
```

### 2. Provider-Specific Setup

#### Google Analytics 4 (GA4)

**Prerequisites**: GA4 official script must load BEFORE measurement snippet.

```html
<!-- 1. Official GA4 script (REQUIRED) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>

<!-- 2. Measurement snippet -->
<script src="./dist/measurement/snippet.iife.min.js"></script>
<script>
  window.MeasurementSnippet.init({
    provider: 'ga4',
    siteId: 'GA_MEASUREMENT_ID',
  });
</script>
```

#### Plausible Analytics

**Prerequisites**: Plausible script must load BEFORE measurement snippet.

```html
<!-- 1. Official Plausible script (REQUIRED) -->
<script defer data-domain="yourdomain.com" src="https://plausible.io/js/script.js"></script>

<!-- 2. Measurement snippet -->
<script src="./dist/measurement/snippet.iife.min.js"></script>
<script>
  window.MeasurementSnippet.init({
    provider: 'plausible',
    siteId: 'yourdomain.com',
  });
</script>
```

### 3. Environment Configuration

#### Development
```javascript
// Disable tracking in development
if (window.location.hostname === 'localhost') {
  // Skip initialization or use test IDs
  console.log('Analytics disabled in development');
} else {
  window.MeasurementSnippet.init({
    provider: 'ga4',
    siteId: 'GA_MEASUREMENT_ID',
  });
}
```

#### Staging vs Production
```javascript
const isProduction = window.location.hostname === 'yourproductionsite.com';

window.MeasurementSnippet.init({
  provider: 'ga4',
  siteId: isProduction ? 'GA_PRODUCTION_ID' : 'GA_STAGING_ID',
});
```

## Privacy & Security Policy

### Data Collection Principles

**Allowed Data**:
- Page URL (`window.location.href`)
- Page title (`document.title`)
- Referrer information (via browser defaults)
- Click targets and metadata (href, category, action, label)

**Prohibited Data (PII)**:
- Personal identifiable information (email, names, addresses)
- Form input values
- Local storage contents
- Authentication tokens or session data
- Device fingerprinting data
- User agent string (beyond browser defaults)

### Security Considerations

#### Content Security Policy (CSP)
When using inline scripts:
```html
<!-- If CSP blocks inline scripts -->
<script src="./dist/measurement/snippet.iife.min.js" nonce="your-nonce"></script>
```

External distribution option:
```html
<!-- For strict CSP environments -->
<script src="https://cdn.yoursite.com/measurement/snippet.iife.min.js"></script>
```

#### No Script Graceful Degradation
The measurement snippet is designed to:
- Never block page rendering
- Fail silently without breaking functionality
- Work in SSR environments without side effects

## API Reference

### Core Functions

```typescript
// Initialize tracking
init(config: {
  provider: 'ga4' | 'plausible';
  siteId?: string;
  enableSPA?: boolean;
  redirectMode?: 'direct' | 'proxy'; // Future: Phase 1.2
}): void

// Manual pageview tracking
trackPageview(): void

// Manual click tracking
trackClick(element: HTMLElement, meta?: {
  category?: string;
  action?: string;
  label?: string;
  value?: number;
}): void

// Decorate single outbound link
decorateOutbound(element: HTMLElement): void

// Auto-decorate all outbound links
decorateAllOutbound(): void
```

### SPA Integration

For single-page applications:
```javascript
window.MeasurementSnippet.init({
  provider: 'ga4',
  siteId: 'GA_MEASUREMENT_ID',
  enableSPA: true, // Automatically tracks navigation
});

// Manual tracking for custom routing
window.addEventListener('route-change', () => {
  window.MeasurementSnippet.trackPageview();
});
```

## Troubleshooting

### Common Issues

**1. Events not appearing in analytics**
- Check if provider script loads before measurement snippet
- Verify provider function exists: `console.log(window.gtag || window.plausible)`
- Check browser console for JavaScript errors

**2. Duplicate events**
- The snippet includes built-in deduplication
- Avoid calling `trackPageview()` multiple times for the same URL
- Click tracking has 1-second cooldown per element

**3. CSP violations**
- Use external script distribution for strict CSP
- Add nonce attribute to script tags
- Consider `script-src 'unsafe-inline'` if necessary

### Debug Mode
```javascript
// Enable debug logging (development only)
window.__measurementDebug = true;

window.MeasurementSnippet.init({
  provider: 'ga4',
  siteId: 'GA_MEASUREMENT_ID',
});
```

## Future Roadmap

### Phase 1.2 Features
- Proxy redirection mode (`/r/:id` endpoints)
- Enhanced conversion tracking
- Cross-domain measurement
- A/B testing integration

The current implementation provides forward-compatible APIs for these features.