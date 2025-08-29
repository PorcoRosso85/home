// Test script to generate many logs with staging protection
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // Staging protection
    const SECRET_HEADER = "X-Staging-Access-Key";
    const SECRET_VALUE = env.STAGING_SECRET || "test-staging-secret-2024";
    
    const incomingSecret = request.headers.get(SECRET_HEADER);
    
    // Allow localhost access without secret for development
    const isLocalhost = url.hostname === 'localhost' || url.hostname === '127.0.0.1';
    
    if (!isLocalhost && incomingSecret !== SECRET_VALUE) {
      console.log(JSON.stringify({
        type: 'security',
        level: 'warn',
        message: 'Unauthorized access attempt',
        data: {
          ip: request.headers.get('CF-Connecting-IP') || 'unknown',
          userAgent: request.headers.get('User-Agent'),
          timestamp: Date.now()
        }
      }));
      return new Response("Forbidden: Missing or invalid secret header", { status: 403 });
    }
    
    if (url.pathname === '/generate-logs') {
      const count = parseInt(url.searchParams.get('count') || '150');
      
      // Generate specified number of log entries
      for (let i = 1; i <= count; i++) {
        console.log(JSON.stringify({
          type: 'test_log',
          index: i,
          timestamp: Date.now(),
          message: `Test log entry number ${i} of ${count}`,
          data: {
            id: crypto.randomUUID(),
            batch: Math.floor(i / 10),
            random: Math.random()
          }
        }));
      }
      
      return new Response(`Generated ${count} log entries`, {
        headers: { 'Content-Type': 'text/plain' }
      });
    }
    
    return new Response('Test Log Generator\nUse /generate-logs?count=150 to generate logs', {
      headers: { 'Content-Type': 'text/plain' }
    });
  }
};