# Analytics Provider Integration Guide

This guide covers integration with supported analytics providers and CSP (Content Security Policy) considerations.

## Global API Reference

### Primary API: `pSEO`

The measurement snippet exposes a global `pSEO` object when loaded as an IIFE (Immediately Invoked Function Expression). This is the **primary and recommended API** for browser environments.

**Available Methods:**
```javascript
// Initialize with provider configuration
pSEO.init({ provider: 'ga4', siteId: 'GA_MEASUREMENT_ID' });

// Track page views (usually automatic with enableSPA: true)
pSEO.trackPageview();

// Track click events with optional metadata
pSEO.trackClick(element, { category: 'button', action: 'signup' });

// Automatically decorate all outbound links with tracking
pSEO.decorateAllOutbound();

// Decorate a specific element with outbound tracking
pSEO.decorateOutbound(linkElement);
```

### Alternative API: `window.MeasurementSnippet`

The snippet also exposes `window.MeasurementSnippet` with identical functionality. This is provided for:
- **Advanced integration scenarios** where global name conflicts occur
- **Library authors** who want to avoid potential `pSEO` naming conflicts
- **Debugging and introspection** of the measurement system

**Usage Example:**
```javascript
// Identical functionality to pSEO
window.MeasurementSnippet.init({ provider: 'ga4', siteId: 'GA_MEASUREMENT_ID' });
window.MeasurementSnippet.decorateAllOutbound();
```

### ESM Import API

For modern JavaScript environments, use ESM imports instead of globals:

```javascript
import { init, trackPageview, trackClick, decorateAllOutbound, decorateOutbound } from './dist/measurement/snippet.esm.js';

init({ provider: 'ga4', siteId: 'GA_MEASUREMENT_ID' });
decorateAllOutbound();
```

**Recommendation:** Use ESM imports when possible for better tree-shaking and explicit dependencies. Use `pSEO` global for simple integrations and legacy environments.

## Supported Providers

### Google Analytics 4 (GA4)

**Setup Requirements:**
1. Load the official GA4 library before the measurement snippet
2. Ensure `window.gtag` is available
3. Configure with your GA4 Measurement ID

**Basic Integration:**
```html
<!-- Load GA4 first -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>

<!-- Load measurement snippet -->
<script src="./dist/measurement/snippet.iife.js"></script>
<script>
  pSEO.init({
    provider: 'ga4',
    siteId: 'GA_MEASUREMENT_ID',
    enableSPA: true
  });
  pSEO.decorateAllOutbound();
</script>
```

**Events Sent:**
- Pageviews: `gtag('event', 'page_view', { page_title, page_location })`
- Clicks: `gtag('event', 'click', { event_category, event_label, value })`

### Plausible Analytics

**Setup Requirements:**
1. Load the official Plausible script before the measurement snippet
2. Ensure `window.plausible` is available
3. Configure with your site domain

**Basic Integration:**
```html
<!-- Load Plausible first -->
<script defer data-domain="yourdomain.com" src="https://plausible.io/js/script.js"></script>

<!-- Load measurement snippet -->
<script src="./dist/measurement/snippet.iife.js"></script>
<script>
  pSEO.init({
    provider: 'plausible',
    siteId: 'yourdomain.com',
    enableSPA: true
  });
  pSEO.decorateAllOutbound();
</script>
```

**Events Sent:**
- Pageviews: `plausible('pageview')`
- Clicks: `plausible('click', { props: { event_category, event_label, value } })`

## Content Security Policy (CSP) Integration

### Strict CSP Environment

For environments with strict CSP that blocks inline scripts, use the external IIFE approach:

**CSP Header Example:**
```
Content-Security-Policy: script-src 'self' 'nonce-YOUR_NONCE' https://www.googletagmanager.com https://plausible.io; object-src 'none'; base-uri 'self';
```

**HTML Structure:**
```html
<!DOCTYPE html>
<html>
<head>
  <!-- CSP header allows external scripts and nonce -->
  <meta http-equiv="Content-Security-Policy" content="script-src 'self' 'nonce-YOUR_NONCE' https://www.googletagmanager.com; object-src 'none';">
</head>
<body>
  <!-- External measurement snippet (CSP compliant) -->
  <script src="./dist/measurement/snippet.iife.js"></script>

  <!-- Provider and initialization (with nonce) -->
  <script nonce="YOUR_NONCE">
    // Provider setup here

    // Initialize measurement
    pSEO.init({ provider: 'ga4', siteId: 'YOUR_ID' });
    pSEO.decorateAllOutbound();
  </script>
</body>
</html>
```

### Nonce Management

**Server-Side Nonce Generation (Example):**
```javascript
// Generate unique nonce per request
const crypto = require('crypto');
const nonce = crypto.randomBytes(16).toString('base64');

// Include in CSP header
res.setHeader('Content-Security-Policy', `script-src 'self' 'nonce-${nonce}'`);

// Pass to template
res.render('page', { nonce });
```

**Template Usage:**
```html
<script nonce="<%= nonce %>">
  pSEO.init({ provider: 'ga4', siteId: 'YOUR_ID' });
</script>
```

## No-Op Safety

The measurement snippet gracefully handles missing providers:

```javascript
// Safe initialization - no errors if provider unavailable
pSEO.init({ provider: 'ga4', siteId: 'GA_ID' });

// Functions become no-ops if:
// - Provider not detected (window.gtag/window.plausible missing)
// - Running in SSR environment (window undefined)
// - CSP blocks provider scripts
```

## Testing Integration

### Local Testing
1. Start test server: `nix run .#serve-examples`
2. Open http://localhost:8080/examples/phase-1.0/
3. Check browser console for tracking events
4. Test CSP compliance: http://localhost:8080/examples/phase-1.0/csp-test.html

### Manual Verification Steps

**GA4 Integration:**
1. Open browser developer tools
2. Navigate to Network tab
3. Load page with measurement snippet
4. Look for requests to `google-analytics.com` or `googletagmanager.com`
5. Check console for `gtag` function calls

**Plausible Integration:**
1. Open browser developer tools
2. Navigate to Network tab
3. Load page with measurement snippet
4. Look for requests to `plausible.io`
5. Check console for `plausible` function calls

**CSP Compliance:**
1. Load CSP test page
2. Check browser console for CSP violations (should be none)
3. Verify external script loading works
4. Test that inline scripts are blocked (as expected)

## Troubleshooting

### Common Issues

**Provider Not Detected:**
- Verify provider script loads before measurement snippet
- Check for JavaScript errors preventing provider initialization
- Ensure CSP allows provider domain

**CSP Violations:**
- Use external script loading (not inline)
- Add provider domains to script-src directive
- Use nonce for initialization scripts

**No Tracking Events:**
- Verify provider is properly initialized
- Check browser network tab for outgoing requests
- Enable console logging to see measurement snippet calls

### Debug Mode

Enable debug logging in development:
```javascript
// Add to browser console
window.DEBUG_MEASUREMENT = true;

// Measurement snippet will log all operations
pSEO.trackPageview(); // Logs: "Pageview tracked via ga4"
```

## Provider-Specific Notes

### GA4 Configuration
- Use Universal Analytics ID format: `G-XXXXXXXXXX`
- Enhanced ecommerce events supported through custom click metadata
- Automatic page_title and page_location parameters

### Plausible Configuration
- Domain must match exactly (no subdomains unless configured)
- Custom event properties passed via `props` object
- Respects plausible.io privacy settings

### Future Providers
The measurement snippet is designed to be extensible. Adding new providers requires:
1. Provider detection function in `getProviderFunction()`
2. Event mapping in `trackPageview()` and `trackClick()`
3. Documentation update in this file

## Security Considerations

- **Provider Scripts**: Only load from official CDNs
- **CSP Configuration**: Use strict policies, allow only necessary domains
- **Nonce Rotation**: Generate unique nonces per request
- **Input Validation**: Measurement snippet validates all inputs
- **No PII**: Avoid passing personal information in tracking parameters
