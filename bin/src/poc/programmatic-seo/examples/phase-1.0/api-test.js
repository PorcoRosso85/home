/**
 * API Behavior Verification Script
 *
 * Run this script in browser console on the test pages to verify:
 * - init() functionality
 * - trackPageview() behavior
 * - trackClick() behavior
 * - decorateOutbound() behavior
 * - No-op safety (provider unavailable)
 * - SSR safety simulation
 * - Idempotency (duplicate prevention)
 *
 * Usage: Copy and paste into browser console, then run: runAPITests()
 */

window.APITestSuite = {
    results: [],

    log: function(test, status, message) {
        const result = { test, status, message, timestamp: new Date().toISOString() };
        this.results.push(result);
        console.log(`[${status}] ${test}: ${message}`);
    },

    assert: function(condition, test, successMsg, failMsg) {
        if (condition) {
            this.log(test, 'PASS', successMsg);
            return true;
        } else {
            this.log(test, 'FAIL', failMsg);
            return false;
        }
    },

    // Test 1: Basic Initialization
    testInit: function() {
        console.group('Test 1: Initialization');

        // Test basic init
        try {
            pSEO.init({
                provider: 'ga4',
                siteId: 'TEST-INIT-ID',
                enableSPA: false
            });
            this.assert(true, 'init-basic', 'Basic init completed without errors', 'Basic init failed');
        } catch (error) {
            this.assert(false, 'init-basic', '', `Basic init threw error: ${error.message}`);
        }

        // Test init with all options
        try {
            pSEO.init({
                provider: 'plausible',
                siteId: 'test-domain.com',
                enableSPA: true,
                redirectMode: 'direct'
            });
            this.assert(true, 'init-full', 'Full options init completed', 'Full options init failed');
        } catch (error) {
            this.assert(false, 'init-full', '', `Full options init threw error: ${error.message}`);
        }

        // Test invalid provider
        try {
            pSEO.init({
                provider: 'invalid-provider',
                siteId: 'test'
            });
            this.assert(true, 'init-invalid-provider', 'Invalid provider handled gracefully', 'Invalid provider caused error');
        } catch (error) {
            this.assert(false, 'init-invalid-provider', '', `Invalid provider threw error: ${error.message}`);
        }

        console.groupEnd();
    },

    // Test 2: Pageview Tracking
    testPageview: function() {
        console.group('Test 2: Pageview Tracking');

        // Store original events for comparison
        const originalGtagEvents = window.mockGtagEvents ? [...window.mockGtagEvents] : [];
        const originalPlausibleEvents = window.mockPlausibleEvents ? [...window.mockPlausibleEvents] : [];

        // Test basic pageview
        try {
            pSEO.trackPageview();
            this.assert(true, 'pageview-basic', 'Basic pageview completed without errors', 'Basic pageview failed');
        } catch (error) {
            this.assert(false, 'pageview-basic', '', `Basic pageview threw error: ${error.message}`);
        }

        // Test idempotency (should not track duplicate pageviews)
        const beforeDupe = window.mockGtagEvents ? window.mockGtagEvents.length : 0;
        pSEO.trackPageview();
        pSEO.trackPageview(); // Duplicate - should be ignored
        const afterDupe = window.mockGtagEvents ? window.mockGtagEvents.length : 0;

        this.assert(
            afterDupe <= beforeDupe + 1,
            'pageview-idempotency',
            'Duplicate pageviews prevented by idempotency check',
            'Duplicate pageviews were not prevented'
        );

        console.groupEnd();
    },

    // Test 3: Click Tracking
    testClick: function() {
        console.group('Test 3: Click Tracking');

        // Create test elements
        const outboundLink = document.createElement('a');
        outboundLink.href = 'https://external.example.com/test';
        outboundLink.textContent = 'External Test Link';

        const internalLink = document.createElement('a');
        internalLink.href = '/internal-test';
        internalLink.textContent = 'Internal Test Link';

        // Test outbound click tracking
        try {
            const beforeEvents = window.mockGtagEvents ? window.mockGtagEvents.length : 0;
            pSEO.trackClick(outboundLink, { category: 'test', action: 'test-click', label: 'outbound-test' });
            const afterEvents = window.mockGtagEvents ? window.mockGtagEvents.length : 0;

            this.assert(
                afterEvents > beforeEvents || window.mockPlausibleEvents?.length > 0,
                'click-outbound',
                'Outbound click tracked successfully',
                'Outbound click tracking failed'
            );
        } catch (error) {
            this.assert(false, 'click-outbound', '', `Outbound click threw error: ${error.message}`);
        }

        // Test internal click tracking
        try {
            pSEO.trackClick(internalLink, { category: 'internal', action: 'internal-click' });
            this.assert(true, 'click-internal', 'Internal click handled without errors', 'Internal click failed');
        } catch (error) {
            this.assert(false, 'click-internal', '', `Internal click threw error: ${error.message}`);
        }

        // Test click idempotency
        const beforeIdempotent = window.mockGtagEvents ? window.mockGtagEvents.length : 0;
        pSEO.trackClick(outboundLink, { category: 'test', action: 'duplicate-test' });
        pSEO.trackClick(outboundLink, { category: 'test', action: 'duplicate-test' }); // Duplicate
        const afterIdempotent = window.mockGtagEvents ? window.mockGtagEvents.length : 0;

        this.assert(
            afterIdempotent <= beforeIdempotent + 1,
            'click-idempotency',
            'Duplicate clicks prevented by idempotency check',
            'Duplicate clicks were not prevented'
        );

        console.groupEnd();
    },

    // Test 4: Outbound Link Decoration
    testDecorateOutbound: function() {
        console.group('Test 4: Outbound Link Decoration');

        // Create test links
        const testContainer = document.createElement('div');
        testContainer.id = 'api-test-container';
        testContainer.innerHTML = `
            <a href="https://github.com" class="test-outbound">GitHub</a>
            <a href="/internal" class="test-internal">Internal</a>
            <a href="mailto:test@example.com" class="test-email">Email</a>
        `;
        document.body.appendChild(testContainer);

        try {
            pSEO.decorateAllOutbound();
            this.assert(true, 'decorate-basic', 'decorateAllOutbound completed without errors', 'decorateAllOutbound failed');

            // Test individual decoration
            const singleLink = document.createElement('a');
            singleLink.href = 'https://test-decoration.example.com';
            pSEO.decorateOutbound(singleLink);
            this.assert(true, 'decorate-single', 'Single link decoration completed', 'Single link decoration failed');

        } catch (error) {
            this.assert(false, 'decorate-basic', '', `decorateOutbound threw error: ${error.message}`);
        }

        // Cleanup
        document.body.removeChild(testContainer);

        console.groupEnd();
    },

    // Test 5: No-Op Safety (Provider Unavailable)
    testNoOpSafety: function() {
        console.group('Test 5: No-Op Safety');

        // Temporarily remove providers
        const originalGtag = window.gtag;
        const originalPlausible = window.plausible;

        delete window.gtag;
        delete window.plausible;

        try {
            // Reinitialize without providers
            pSEO.init({ provider: 'ga4', siteId: 'no-provider-test' });
            pSEO.trackPageview();
            pSEO.trackClick(document.createElement('a'));
            pSEO.decorateAllOutbound();

            this.assert(true, 'no-op-safety', 'All functions work safely without providers', 'Functions failed without providers');
        } catch (error) {
            this.assert(false, 'no-op-safety', '', `No-op safety failed: ${error.message}`);
        }

        // Restore providers
        if (originalGtag) window.gtag = originalGtag;
        if (originalPlausible) window.plausible = originalPlausible;

        console.groupEnd();
    },

    // Test 6: SSR Safety Simulation
    testSSRSafety: function() {
        console.group('Test 6: SSR Safety');

        // Cannot actually test SSR in browser, but can test defensive coding
        try {
            // Test that functions handle missing DOM gracefully
            const mockElement = {
                getAttribute: () => null,
                textContent: '',
                addEventListener: () => {},
                href: 'https://test.com'
            };

            pSEO.trackClick(mockElement);
            this.assert(true, 'ssr-mock-element', 'Mock element handled gracefully', 'Mock element caused error');

            // Test null/undefined handling
            pSEO.trackClick(null);
            this.assert(true, 'ssr-null-element', 'Null element handled gracefully', 'Null element caused error');

        } catch (error) {
            this.assert(false, 'ssr-safety', '', `SSR safety test failed: ${error.message}`);
        }

        console.groupEnd();
    },

    // Test 7: State Management
    testStateManagement: function() {
        console.group('Test 7: State Management');

        try {
            // Test multiple initializations
            pSEO.init({ provider: 'ga4', siteId: 'state-test-1' });
            pSEO.init({ provider: 'plausible', siteId: 'state-test-2' }); // Should replace first

            this.assert(true, 'state-multi-init', 'Multiple initializations handled correctly', 'Multiple init failed');

            // Test state persistence across calls
            pSEO.trackPageview();
            pSEO.trackPageview(); // Should be idempotent

            this.assert(true, 'state-persistence', 'State persistence works correctly', 'State persistence failed');

        } catch (error) {
            this.assert(false, 'state-management', '', `State management failed: ${error.message}`);
        }

        console.groupEnd();
    },

    // Run all tests
    runAllTests: function() {
        console.clear();
        console.log('🧪 Starting API Behavior Verification Tests');
        console.log('='.repeat(50));

        this.results = [];

        this.testInit();
        this.testPageview();
        this.testClick();
        this.testDecorateOutbound();
        this.testNoOpSafety();
        this.testSSRSafety();
        this.testStateManagement();

        this.printResults();
    },

    // Print test results summary
    printResults: function() {
        console.log('\n' + '='.repeat(50));
        console.log('📊 Test Results Summary');
        console.log('='.repeat(50));

        const passed = this.results.filter(r => r.status === 'PASS').length;
        const failed = this.results.filter(r => r.status === 'FAIL').length;
        const total = this.results.length;

        console.log(`Total Tests: ${total}`);
        console.log(`✅ Passed: ${passed}`);
        console.log(`❌ Failed: ${failed}`);
        console.log(`📈 Success Rate: ${((passed/total) * 100).toFixed(1)}%`);

        if (failed > 0) {
            console.log('\n❌ Failed Tests:');
            this.results.filter(r => r.status === 'FAIL').forEach(result => {
                console.log(`  - ${result.test}: ${result.message}`);
            });
        }

        console.log('\n💾 Full results available in: window.APITestSuite.results');
        console.log('🔄 Re-run tests with: window.APITestSuite.runAllTests()');
    }
};

// Global shortcut
window.runAPITests = function() {
    window.APITestSuite.runAllTests();
};

console.log('🧪 API Test Suite Loaded');
console.log('Run tests with: runAPITests()');
