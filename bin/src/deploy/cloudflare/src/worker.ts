/**
 * RedwoodSDK R2 Resource Management Worker
 * Minimal Worker for Resource Plane operations - health checks and binding verification
 */

// Environment interface for R2 bindings
interface Env {
  // R2 bucket bindings (auto-generated from wrangler.jsonc)
  USER_UPLOADS?: R2Bucket;
  STATIC_ASSETS?: R2Bucket;

  // Additional bindings that might be present
  [key: string]: any;
}


/**
 * Main Worker fetch handler
 */
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    // CORS headers for local development
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    try {
      // Route handling
      switch (path) {
        case '/':
          return handleRoot();

        case '/health':
          return handleHealth();

        case '/bindings':
          return handleBindings(env);

        default:
          return new Response('Not Found', {
            status: 404,
            headers: corsHeaders
          });
      }
    } catch (error) {
      console.error('Worker error:', error);
      return new Response(JSON.stringify({
        error: 'Internal Server Error',
        message: error instanceof Error ? error.message : String(error)
      }), {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
  },
};

/**
 * Root endpoint - basic info
 */
function handleRoot(): Response {
  return new Response(JSON.stringify({
    service: 'RedwoodSDK R2 Resource Management Worker',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
    scope: 'Resource Plane Operations Only',
    endpoints: {
      '/health': 'Health check',
      '/bindings': 'List available R2 bindings'
    }
  }), {
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*'
    }
  });
}

/**
 * Health check endpoint
 */
function handleHealth(): Response {
  return new Response(JSON.stringify({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: Date.now()
  }), {
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*'
    }
  });
}

/**
 * List available R2 bindings
 */
function handleBindings(env: Env): Response {
  const bindings: string[] = [];

  // Check for known R2 bindings
  const knownBindings = ['USER_UPLOADS', 'STATIC_ASSETS'];

  for (const binding of knownBindings) {
    if (env[binding]) {
      bindings.push(binding);
    }
  }

  // Check for any other R2-like bindings
  for (const key of Object.keys(env)) {
    if (key.includes('BUCKET') || key.includes('R2')) {
      if (!bindings.includes(key)) {
        bindings.push(key);
      }
    }
  }

  return new Response(JSON.stringify({
    bindings,
    count: bindings.length,
    message: bindings.length > 0
      ? 'R2 bindings found and configured'
      : 'No R2 bindings found - check wrangler.jsonc configuration'
  }), {
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*'
    }
  });
}

