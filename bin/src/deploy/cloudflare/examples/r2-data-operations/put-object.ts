/**
 * R2 Data Plane Example: PUT Object Operation
 *
 * WARNING: This is an educational sample only.
 * Data Plane operations are NOT part of this flake's scope.
 * This flake manages Control Plane operations only.
 */

export interface Env {
  USER_UPLOADS: R2Bucket;
}

/**
 * Example: Upload object to R2 bucket
 * Data Plane operation - writes actual data to storage
 */
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method !== 'PUT') {
      return new Response('Method not allowed', { status: 405 });
    }

    try {
      const url = new URL(request.url);
      const objectKey = url.pathname.slice(1); // Remove leading /

      if (!objectKey) {
        return new Response('Object key required', { status: 400 });
      }

      // Data Plane operation: Store object in R2
      const object = await env.USER_UPLOADS.put(objectKey, request.body, {
        httpMetadata: {
          contentType: request.headers.get('content-type') || 'application/octet-stream',
        },
        customMetadata: {
          uploadedAt: new Date().toISOString(),
          uploadedBy: 'example-worker'
        }
      });

      return new Response(JSON.stringify({
        success: true,
        key: objectKey,
        etag: object.etag,
        size: object.size,
        message: 'Object uploaded successfully'
      }), {
        headers: { 'Content-Type': 'application/json' }
      });

    } catch (error) {
      return new Response(JSON.stringify({
        error: 'Upload failed',
        message: error instanceof Error ? error.message : String(error)
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }
};