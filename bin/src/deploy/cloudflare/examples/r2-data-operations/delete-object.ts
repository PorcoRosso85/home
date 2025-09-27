/**
 * R2 Data Plane Example: DELETE Object Operation
 *
 * WARNING: This is an educational sample only.
 * Data Plane operations are NOT part of this flake's scope.
 * This flake manages Control Plane operations only.
 */

export interface Env {
  USER_UPLOADS: R2Bucket;
}

/**
 * Example: Delete object from R2 bucket
 * Data Plane operation - removes actual data from storage
 */
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method !== 'DELETE') {
      return new Response('Method not allowed', { status: 405 });
    }

    try {
      const url = new URL(request.url);
      const objectKey = url.pathname.slice(1); // Remove leading /

      if (!objectKey) {
        return new Response('Object key required', { status: 400 });
      }

      // Check if object exists first
      const existingObject = await env.USER_UPLOADS.head(objectKey);
      if (!existingObject) {
        return new Response(JSON.stringify({
          error: 'Object not found',
          key: objectKey
        }), {
          status: 404,
          headers: { 'Content-Type': 'application/json' }
        });
      }

      // Data Plane operation: Delete object from R2
      await env.USER_UPLOADS.delete(objectKey);

      return new Response(JSON.stringify({
        success: true,
        key: objectKey,
        message: 'Object deleted successfully',
        deletedAt: new Date().toISOString()
      }), {
        headers: { 'Content-Type': 'application/json' }
      });

    } catch (error) {
      return new Response(JSON.stringify({
        error: 'Deletion failed',
        message: error instanceof Error ? error.message : String(error)
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }
};