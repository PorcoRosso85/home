#!/bin/bash

echo "=== Cloudflare Logging Test ==="
echo ""
echo "Testing console.log behavior in different environments:"
echo ""

# Create a test worker file
cat > test-worker.js << 'EOF'
export default {
  async fetch(request, env, ctx) {
    // Structured log that Cloudflare can parse
    const logEntry = {
      type: 'form_submission',
      version: 1,
      timestamp: Date.now(),
      data: {
        id: crypto.randomUUID(),
        name: 'Test User',
        email: 'test@example.com',
        subject: 'Test Subject',
        message: 'Test Message',
        submittedAt: new Date().toISOString()
      },
      _metadata: {
        cf_ray: request.headers.get('cf-ray'),
        url: request.url
      }
    };

    // This goes to Cloudflare Logs in production
    console.log(JSON.stringify(logEntry));

    // Also test different log levels
    console.info('INFO: Form submission received');
    console.warn('WARN: High submission rate detected');
    console.error('ERROR: Simulated error for testing');

    return new Response(JSON.stringify({
      message: 'Log test complete',
      logEntry: logEntry
    }), {
      headers: { 'content-type': 'application/json' }
    });
  }
};
EOF

echo "1. Testing with Wrangler (local):"
echo "   Run: npx wrangler dev test-worker.js"
echo "   → Logs appear in terminal"
echo ""

echo "2. Testing with Wrangler + --local=false (edge preview):"
echo "   Run: npx wrangler dev test-worker.js --local=false"
echo "   → Logs appear in terminal AND Cloudflare dashboard"
echo ""

echo "3. Tail production logs:"
echo "   Run: npx wrangler tail waku-init"
echo "   → Real-time log streaming from production"
echo ""

echo "4. Testing current implementation:"
echo "   Checking if our server action logs correctly..."
echo ""

# Test the actual implementation
curl -X POST http://localhost:8787 \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=Test&email=test@example.com&subject=Test&message=Testing" \
  2>/dev/null | jq '.'

echo ""
echo "5. Cloudflare Dashboard locations:"
echo "   • Workers & Pages > waku-init > Logs"
echo "   • Workers & Pages > waku-init > Real-time Logs"
echo "   • Analytics & Logs > Instant Logs"
echo ""

echo "6. Logpush configuration (for production):"
cat > logpush-config.json << 'EOF'
{
  "dataset": "workers_trace_events",
  "destination_conf": "r2://waku-data/logs/{DATE}",
  "filter": {
    "where": {
      "key": "ScriptName",
      "operator": "eq",
      "value": "waku-init"
    }
  },
  "enabled": true
}
EOF

echo "   Created logpush-config.json for R2 storage"
echo ""

echo "7. Analytics Engine setup:"
cat > analytics-engine.js << 'EOF'
// Add to wrangler.toml:
// [[analytics_engine_datasets]]
// binding = "AE"
// dataset = "form_submissions"

export default {
  async fetch(request, env, ctx) {
    // Write to Analytics Engine
    env.AE.writeDataPoint({
      blobs: ['test@example.com', 'Test User'],
      doubles: [Date.now()],
      indexes: ['form_submission']
    });
    
    // Query from Analytics Engine
    const sql = `
      SELECT 
        blob1 as email,
        COUNT(*) as count
      FROM form_submissions
      WHERE index1 = 'form_submission'
      GROUP BY blob1
    `;
    
    return new Response('Analytics Engine data written');
  }
};
EOF

echo "   Created analytics-engine.js example"
echo ""
echo "✅ Test files created. Now run:"
echo "   1. npx wrangler dev test-worker.js"
echo "   2. Check console output for logs"
echo "   3. Deploy and check Cloudflare dashboard"