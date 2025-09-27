/**
 * R2 Data Plane Example: GET Object Operation
 *
 * WARNING: This is an educational sample only.
 * Data Plane operations are NOT part of this flake's scope.
 * This flake manages Control Plane operations only.
 */

export interface Env {
  USER_UPLOADS: R2Bucket;
}

/**
 * Example: Retrieve object from R2 bucket
 * Data Plane operation - reads actual data from storage
 */
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method !== 'GET') {
      return new Response('Method not allowed', { status: 405 });
    }

    try {
      const url = new URL(request.url);
      const objectKey = url.pathname.slice(1); // Remove leading /

      if (!objectKey) {
        return new Response('Object key required', { status: 400 });
      }

      // Data Plane operation: Retrieve object from R2
      const object = await env.USER_UPLOADS.get(objectKey);

      if (!object) {
        return new Response('Object not found', { status: 404 });
      }

      // Handle range requests
      const range = request.headers.get('range');
      if (range) {
        const rangeResponse = await env.USER_UPLOADS.get(objectKey, {
          range: request.headers
        });

        if (rangeResponse && rangeResponse.body) {
          return new Response(rangeResponse.body, {
            status: 206,
            headers: {
              'Content-Type': object.httpMetadata?.contentType || 'application/octet-stream',
              'Content-Range': rangeResponse.range?.toString() || '',
              'Content-Length': rangeResponse.size?.toString() || '0',
              'ETag': object.etag,
              'Last-Modified': object.uploaded.toUTCString()
            }
          });
        }
      }

      // Return full object
      return new Response(object.body, {
        headers: {
          'Content-Type': object.httpMetadata?.contentType || 'application/octet-stream',
          'Content-Length': object.size.toString(),
          'ETag': object.etag,
          'Last-Modified': object.uploaded.toUTCString(),
          'Cache-Control': 'public, max-age=3600'
        }
      });

    } catch (error) {
      return new Response(JSON.stringify({
        error: 'Retrieval failed',
        message: error instanceof Error ? error.message : String(error)
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }
};