'use server';

import { getHonoContext } from '../../waku.hono-enhancer';

interface DatabaseInfo {
  name: string;
  size: number;
  uploaded: Date;
  url?: string;
}

/**
 * Server action to list SQLite databases from R2
 */
export async function listDatabases(): Promise<DatabaseInfo[]> {
  const ctx = getHonoContext();
  console.log('listDatabases called, ctx exists:', !!ctx);
  
  if (!ctx) return [];
  
  const env = ctx.env as any;
  const bucket = env.DATA_BUCKET;
  console.log('R2 bucket binding exists:', !!bucket);
  
  if (!bucket) return [];
  
  try {
    const listed = await bucket.list({
      prefix: 'sqlite-databases/',
      limit: 100
    });
    
    console.log('R2 list result:', {
      objects: listed.objects?.length || 0,
      truncated: listed.truncated,
      cursor: listed.cursor
    });
    
    return listed.objects.map((obj: any) => ({
      name: obj.key.replace('sqlite-databases/', ''),
      size: obj.size,
      uploaded: obj.uploaded
    }));
  } catch (error) {
    console.error('Failed to list databases:', error);
    return [];
  }
}

/**
 * Server action to get SQLite database from R2
 */
export async function getDatabase(name: string): Promise<ArrayBuffer> {
  const ctx = getHonoContext();
  if (!ctx) {
    throw new Error('Server context not available');
  }
  
  const env = ctx.env as any;
  const bucket = env.DATA_BUCKET;
  
  if (!bucket) {
    throw new Error('R2 bucket not configured');
  }
  
  try {
    const object = await bucket.get(`sqlite-databases/${name}`);
    if (!object) {
      throw new Error(`Database '${name}' not found in R2`);
    }
    
    return await object.arrayBuffer();
  } catch (error) {
    console.error('Failed to get database:', error);
    throw error;
  }
}

/**
 * Server action to upload SQLite database to R2
 */
export async function uploadDatabase(buffer: ArrayBuffer, name: string): Promise<boolean> {
  const ctx = getHonoContext();
  if (!ctx) return false;
  
  const env = ctx.env as any;
  const bucket = env.DATA_BUCKET;
  
  if (!bucket) return false;
  
  try {
    await bucket.put(`sqlite-databases/${name}`, buffer, {
      httpMetadata: {
        contentType: 'application/x-sqlite3'
      }
    });
    return true;
  } catch (error) {
    console.error('Failed to upload database:', error);
    return false;
  }
}