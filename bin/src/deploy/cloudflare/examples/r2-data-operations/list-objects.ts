/**
 * R2 Data Plane Example: LIST Objects Operation
 *
 * WARNING: This is an educational sample only.
 * Data Plane operations are NOT part of this flake's scope.
 * This flake manages Control Plane operations only.
 */

export interface Env {
  USER_UPLOADS: R2Bucket;
}

/**
 * Example: List objects in R2 bucket
 * Data Plane operation - queries actual data metadata from storage
 */
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method !== 'GET') {
      return new Response('Method not allowed', { status: 405 });
    }

    try {
      const url = new URL(request.url);
      const searchParams = url.searchParams;

      // Parse query parameters for listing options
      const prefix = searchParams.get('prefix') || undefined;
      const delimiter = searchParams.get('delimiter') || undefined;
      const cursor = searchParams.get('cursor') || undefined;
      const limit = searchParams.get('limit') ? parseInt(searchParams.get('limit')!) : 100;

      // Data Plane operation: List objects in R2 bucket
      const listing = await env.USER_UPLOADS.list({
        prefix,
        delimiter,
        cursor,
        limit: Math.min(limit, 1000) // Cap at 1000 for safety
      });

      // Format response
      const response = {
        objects: listing.objects.map(obj => ({
          key: obj.key,
          size: obj.size,
          etag: obj.etag,
          uploaded: obj.uploaded.toISOString(),
          httpMetadata: obj.httpMetadata,
          customMetadata: obj.customMetadata
        })),
        truncated: listing.truncated,
        cursor: listing.cursor,
        delimitedPrefixes: listing.delimitedPrefixes || [],
        totalCount: listing.objects.length,
        queryParameters: {
          prefix,
          delimiter,
          limit,
          cursor
        }
      };

      return new Response(JSON.stringify(response, null, 2), {
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache' // Listings should not be cached
        }
      });

    } catch (error) {
      return new Response(JSON.stringify({
        error: 'Listing failed',
        message: error instanceof Error ? error.message : String(error)
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }
};