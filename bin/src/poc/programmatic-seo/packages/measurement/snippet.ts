/**
 * Programmatic SEO Measurement Snippet
 * Zero-overhead analytics for server-side and client-side environments
 */

type ProviderType = 'ga4' | 'plausible';

type MeasurementConfig = {
  provider: ProviderType;
  siteId?: string;
  enableSPA?: boolean;
  redirectMode?: 'direct' | 'proxy'; // Future: /r/:id support
};

type ClickMeta = {
  category?: string;
  action?: string;
  label?: string;
  value?: number;
};

type MeasurementState = {
  initialized: boolean;
  config: MeasurementConfig | null;
  inflightRequests: Set<string>;
  clickHistory: Map<string, number>;
  lastPageview: string | null;
};

// Global state with SSR safety
const getState = (): MeasurementState => {
  if (typeof window === 'undefined') {
    return {
      initialized: false,
      config: null,
      inflightRequests: new Set(),
      clickHistory: new Map(),
      lastPageview: null,
    };
  }

  if (!(window as any).__measurementState) {
    (window as any).__measurementState = {
      initialized: false,
      config: null,
      inflightRequests: new Set(),
      clickHistory: new Map(),
      lastPageview: null,
    };
  }

  return (window as any).__measurementState as MeasurementState;
};

// Provider detection and delegation
const getProviderFunction = (provider: ProviderType): ((event: string, data: Record<string, unknown>) => void) | null => {
  if (typeof window === 'undefined') return null;

  const win = window as any;

  switch (provider) {
    case 'ga4':
      return typeof win.gtag === 'function' ? win.gtag as ((event: string, data: Record<string, unknown>) => void) : null;
    case 'plausible':
      return typeof win.plausible === 'function' ? win.plausible as ((event: string, data: Record<string, unknown>) => void) : null;
    default:
      return null;
  }
};

// Idempotency guard for clicks
const generateClickKey = (element: HTMLElement, meta?: ClickMeta): string => {
  const href = element.getAttribute('href') || '';
  const text = element.textContent?.slice(0, 50) || '';
  const metaKey = meta ? JSON.stringify(meta) : '';
  return `${href}:${text}:${metaKey}`;
};

const isRecentClick = (clickKey: string, threshold = 1000): boolean => {
  const state = getState();
  const lastClick = state.clickHistory.get(clickKey);
  const now = Date.now();

  if (lastClick && (now - lastClick) < threshold) {
    return true;
  }

  state.clickHistory.set(clickKey, now);

  // Cleanup old entries (keep last 100)
  if (state.clickHistory.size > 100) {
    const entries = Array.from(state.clickHistory.entries());
    entries.sort((a, b) => b[1] - a[1]);
    state.clickHistory = new Map(entries.slice(0, 100));
  }

  return false;
};

// URL classification
const isOutboundLink = (href: string): boolean => {
  if (typeof window === 'undefined') return false;

  try {
    const url = new URL(href, window.location.href);
    return url.hostname !== window.location.hostname;
  } catch {
    return false;
  }
};

// Core API
export const init = (config: MeasurementConfig): void => {
  if (typeof window === 'undefined') return; // SSR safety

  const state = getState();
  state.config = config;
  state.initialized = true;

  // SPA support: Auto pageview tracking
  if (config.enableSPA && typeof window !== 'undefined') {
    const originalPushState = window.history.pushState;
    const originalReplaceState = window.history.replaceState;

    window.history.pushState = function(...args) {
      originalPushState.apply(this, args);
      setTimeout(() => trackPageview(), 0);
    };

    window.history.replaceState = function(...args) {
      originalReplaceState.apply(this, args);
      setTimeout(() => trackPageview(), 0);
    };

    window.addEventListener('popstate', () => {
      setTimeout(() => trackPageview(), 0);
    });
  }
};

export const trackPageview = (): void => {
  if (typeof window === 'undefined') return; // SSR safety

  const state = getState();
  if (!state.initialized || !state.config) return;

  const currentUrl = window.location.href;
  if (state.lastPageview === currentUrl) return; // Avoid duplicate pageviews

  const providerFn = getProviderFunction(state.config.provider);
  if (!providerFn) return; // No-op if provider not available

  const pageData = {
    page_location: currentUrl,
    page_title: document.title,
  };

  state.lastPageview = currentUrl;

  try {
    if (state.config.provider === 'ga4') {
      providerFn('config', { page_title: document.title, page_location: currentUrl });
    } else if (state.config.provider === 'plausible') {
      providerFn('pageview', pageData);
    }
  } catch (error) {
    // Silent fail - don't break user experience
    console.warn('Measurement tracking failed:', error);
  }
};

export const trackClick = (element: HTMLElement, meta?: ClickMeta): void => {
  if (typeof window === 'undefined') return; // SSR safety

  const state = getState();
  if (!state.initialized || !state.config) return;

  const clickKey = generateClickKey(element, meta);
  if (isRecentClick(clickKey)) return; // Prevent duplicate clicks

  const providerFn = getProviderFunction(state.config.provider);
  if (!providerFn) return; // No-op if provider not available

  const href = element.getAttribute('href') || '';
  const isOutbound = isOutboundLink(href);

  const eventData = {
    event_category: meta?.category || (isOutbound ? 'outbound' : 'internal'),
    event_label: meta?.label || href,
    value: meta?.value,
    ...meta,
  };

  try {
    if (state.config.provider === 'ga4') {
      (providerFn as any)('event', meta?.action || 'click', eventData);
    } else if (state.config.provider === 'plausible') {
      (providerFn as any)(meta?.action || 'click', { props: eventData });
    }
  } catch (error) {
    // Silent fail - don't break user experience
    console.warn('Click tracking failed:', error);
  }
};

export const decorateOutbound = (element: HTMLElement): void => {
  if (typeof window === 'undefined') return; // SSR safety

  const href = element.getAttribute('href');
  if (!href || !isOutboundLink(href)) return;

  // Future: Support proxy mode for /r/:id redirection
  const state = getState();
  const redirectMode = state.config?.redirectMode || 'direct';

  if (redirectMode === 'direct') {
    // Current implementation: Direct tracking
    element.addEventListener('click', (event) => {
      trackClick(element, { category: 'outbound', action: 'click', label: href });

      // Use Beacon API for reliable tracking before navigation
      if (typeof navigator !== 'undefined' && typeof navigator.sendBeacon === 'function') {
        // Additional beacon tracking can be added here if needed
      }
    }, { passive: true });
  } else if (redirectMode === 'proxy') {
    // Future: Proxy through /r/:id endpoint
    // This will be implemented in Phase 1.2
    console.warn('Proxy redirect mode not yet implemented');
  }
};

// Auto-decoration helper for existing links
export const decorateAllOutbound = (): void => {
  if (typeof window === 'undefined') return; // SSR safety

  const links = document.querySelectorAll('a[href]');
  links.forEach((link) => {
    if (link instanceof HTMLElement) {
      decorateOutbound(link);
    }
  });
};

// Export for IIFE build
if (typeof window !== 'undefined') {
  (window as any).MeasurementSnippet = {
    init,
    trackPageview,
    trackClick,
    decorateOutbound,
    decorateAllOutbound,
  };
}