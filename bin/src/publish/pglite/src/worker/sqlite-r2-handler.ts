// SQLite database management via R2
// Handles upload, fetch, and serving of SQLite databases

interface Env {
  DATA_BUCKET: R2Bucket;
  R2_PUBLIC_URL?: string;
}

export async function handleSQLiteR2Request(
  request: Request,
  env: Env,
  ctx: ExecutionContext
): Promise<Response> {
  const url = new URL(request.url);
  const pathname = url.pathname;

  // Route: GET /api/sqlite/db/{dbname}
  // Fetch SQLite database from R2
  if (pathname.startsWith('/api/sqlite/db/') && request.method === 'GET') {
    const dbName = pathname.replace('/api/sqlite/db/', '');
    
    if (!dbName || dbName.includes('..')) {
      return new Response('Invalid database name', { status: 400 });
    }

    try {
      const dbPath = `sqlite-databases/${dbName}`;
      const object = await env.DATA_BUCKET.get(dbPath);
      
      if (!object) {
        return new Response('Database not found', { status: 404 });
      }

      // Return database with proper headers for CORS and caching
      const headers = new Headers({
        'Content-Type': 'application/x-sqlite3',
        'Cache-Control': 'public, max-age=3600',
        'Access-Control-Allow-Origin': '*',
        'X-Database-Size': object.size.toString(),
        'X-Database-Modified': object.uploaded.toISOString()
      });

      return new Response(object.body, { headers });
    } catch (error) {
      console.error('Error fetching database:', error);
      return new Response('Failed to fetch database', { status: 500 });
    }
  }

  // Route: POST /api/sqlite/upload
  // Upload SQLite database to R2
  if (pathname === '/api/sqlite/upload' && request.method === 'POST') {
    try {
      const formData = await request.formData();
      const file = formData.get('database') as File;
      const name = formData.get('name') as string || file.name;
      
      if (!file) {
        return new Response('No database file provided', { status: 400 });
      }

      // Validate SQLite file (check magic bytes)
      const buffer = await file.arrayBuffer();
      const bytes = new Uint8Array(buffer);
      const magic = new TextDecoder().decode(bytes.slice(0, 16));
      
      if (!magic.startsWith('SQLite format 3')) {
        return new Response('Invalid SQLite database file', { status: 400 });
      }

      // Upload to R2
      const dbPath = `sqlite-databases/${name}`;
      await env.DATA_BUCKET.put(dbPath, buffer, {
        httpMetadata: {
          contentType: 'application/x-sqlite3'
        },
        customMetadata: {
          uploadedAt: new Date().toISOString(),
          originalName: file.name,
          size: buffer.byteLength.toString()
        }
      });

      // Generate public URL if available
      const publicUrl = env.R2_PUBLIC_URL 
        ? `${env.R2_PUBLIC_URL}/${dbPath}`
        : `/api/sqlite/db/${name}`;

      return new Response(JSON.stringify({
        success: true,
        name,
        path: dbPath,
        url: publicUrl,
        size: buffer.byteLength
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (error) {
      console.error('Error uploading database:', error);
      return new Response('Failed to upload database', { status: 500 });
    }
  }

  // Route: GET /api/sqlite/list
  // List available SQLite databases
  if (pathname === '/api/sqlite/list' && request.method === 'GET') {
    try {
      const listed = await env.DATA_BUCKET.list({
        prefix: 'sqlite-databases/',
        limit: 100
      });

      const databases = listed.objects.map(obj => ({
        name: obj.key.replace('sqlite-databases/', ''),
        size: obj.size,
        uploaded: obj.uploaded,
        url: env.R2_PUBLIC_URL 
          ? `${env.R2_PUBLIC_URL}/${obj.key}`
          : `/api/sqlite/db/${obj.key.replace('sqlite-databases/', '')}`
      }));

      return new Response(JSON.stringify({
        databases,
        truncated: listed.truncated
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (error) {
      console.error('Error listing databases:', error);
      return new Response('Failed to list databases', { status: 500 });
    }
  }

  // Route: DELETE /api/sqlite/db/{dbname}
  // Delete SQLite database from R2
  if (pathname.startsWith('/api/sqlite/db/') && request.method === 'DELETE') {
    const dbName = pathname.replace('/api/sqlite/db/', '');
    
    if (!dbName || dbName.includes('..')) {
      return new Response('Invalid database name', { status: 400 });
    }

    try {
      const dbPath = `sqlite-databases/${dbName}`;
      await env.DATA_BUCKET.delete(dbPath);
      
      return new Response(JSON.stringify({
        success: true,
        message: `Database ${dbName} deleted`
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (error) {
      console.error('Error deleting database:', error);
      return new Response('Failed to delete database', { status: 500 });
    }
  }

  return new Response('Not Found', { status: 404 });
}

// Helper function to create sample SQLite database
export async function createSampleDatabase(): Promise<ArrayBuffer> {
  // This would use official SQLite WASM to create a database
  // For now, return a placeholder
  const encoder = new TextEncoder();
  const header = encoder.encode('SQLite format 3\x00');
  const buffer = new ArrayBuffer(1024);
  const view = new Uint8Array(buffer);
  view.set(header, 0);
  return buffer;
}