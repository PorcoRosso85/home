/**
 * RedwoodSDK R2 Connection Test Worker
 * Minimal Worker for testing R2 bucket operations in local development mode
 */

// Environment interface for R2 bindings
interface Env {
  // R2 bucket bindings (auto-generated from wrangler.jsonc)
  USER_UPLOADS?: R2Bucket;
  STATIC_ASSETS?: R2Bucket;

  // Additional bindings that might be present
  [key: string]: any;
}

// Request/Response types for R2 testing
interface R2TestRequest {
  operation: string;
  key: string;
  content: string;
}

interface R2TestResponse {
  success: boolean;
  message: string;
  retrieved?: string;
  error?: string;
  bindings?: string[];
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

        case '/r2-test':
          return handleR2Test(request, env);

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
    service: 'RedwoodSDK R2 Local Test Worker',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
    endpoints: {
      '/health': 'Health check',
      '/bindings': 'List available R2 bindings',
      '/r2-test': 'Test R2 operations (POST)'
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
      ? 'R2 bindings found and ready for testing'
      : 'No R2 bindings found - check wrangler.jsonc configuration'
  }), {
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*'
    }
  });
}

/**
 * R2 test operations endpoint
 */
async function handleR2Test(request: Request, env: Env): Promise<Response> {
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({
      success: false,
      error: 'Method not allowed',
      message: 'Use POST method for R2 testing'
    }), {
      status: 405,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    });
  }

  try {
    const data = await request.json() as R2TestRequest;
    const { operation, key, content } = data;

    // Validate input
    if (!operation || !key || !content) {
      return new Response(JSON.stringify({
        success: false,
        error: 'Invalid request',
        message: 'Missing required fields: operation, key, content'
      }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      });
    }

    // Get the first available R2 binding for testing
    const bucket = env.USER_UPLOADS || env.STATIC_ASSETS;

    if (!bucket) {
      const availableBindings = Object.keys(env).filter(key =>
        env[key] && typeof env[key] === 'object' && 'put' in env[key]
      );

      return new Response(JSON.stringify({
        success: false,
        error: 'No R2 binding found',
        message: `No R2 bucket binding available. Check wrangler.jsonc r2_buckets configuration.`,
        bindings: availableBindings
      }), {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      });
    }

    // Perform R2 operations based on the operation type
    switch (operation) {
      case 'test-connection':
        return await performR2Test(bucket, key, content);

      default:
        return new Response(JSON.stringify({
          success: false,
          error: 'Unknown operation',
          message: `Supported operations: test-connection`
        }), {
          status: 400,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          }
        });
    }

  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      error: 'Request processing failed',
      message: error instanceof Error ? error.message : String(error)
    }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    });
  }
}

/**
 * Perform comprehensive R2 testing
 */
async function performR2Test(bucket: R2Bucket, key: string, content: string): Promise<Response> {
  try {
    const testResults: string[] = [];

    // Test 1: HEAD operation (check if object exists)
    try {
      await bucket.head(key);
      testResults.push('HEAD: Object exists (will be overwritten)');
    } catch (e) {
      testResults.push('HEAD: Object does not exist (expected for new test)');
    }

    // Test 2: PUT operation
    await bucket.put(key, content, {
      metadata: {
        testTimestamp: new Date().toISOString(),
        testPurpose: 'R2 connection verification'
      }
    });
    testResults.push('PUT: Successfully stored object');

    // Test 3: GET operation
    const object = await bucket.get(key);
    if (!object) {
      throw new Error('GET: Object not found after PUT operation');
    }

    const retrieved = await object.text();
    testResults.push('GET: Successfully retrieved object');

    // Test 4: Content verification
    if (retrieved === content) {
      testResults.push('VERIFY: Content matches original');
    } else {
      throw new Error(`VERIFY: Content mismatch. Expected: "${content}", Got: "${retrieved}"`);
    }

    // Test 5: Metadata verification
    const metadata = object.metadata;
    if (metadata?.testTimestamp) {
      testResults.push('METADATA: Successfully stored and retrieved');
    }

    // Test 6: DELETE operation (cleanup)
    await bucket.delete(key);
    testResults.push('DELETE: Successfully cleaned up test object');

    // Final verification - object should be gone
    const deletedObject = await bucket.get(key);
    if (deletedObject === null) {
      testResults.push('CLEANUP: Object successfully deleted');
    } else {
      testResults.push('CLEANUP: Warning - object still exists after delete');
    }

    const response: R2TestResponse = {
      success: true,
      message: 'All R2 operations completed successfully',
      retrieved,
      bindings: ['R2 bucket binding operational']
    };

    return new Response(JSON.stringify(response), {
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    });

  } catch (error) {
    const response: R2TestResponse = {
      success: false,
      message: 'R2 operation failed',
      error: error instanceof Error ? error.message : String(error)
    };

    return new Response(JSON.stringify(response), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    });
  }
}