// Test script to generate many logs
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
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