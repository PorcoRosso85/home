import { writeFileSync } from 'fs';
import { createRequire } from 'module';

// Use require for Node.js environment
const require = createRequire(import.meta.url);
const kuzu = require('kuzu-wasm/nodejs');

export type ExportFormat = 'parquet' | 'csv';

export type ExportOptions = {
  format?: ExportFormat;
  outputPath?: string;
  query: string;
};

export type ExportSuccess = {
  path: string;
  size: number;
};

export type ExportError = {
  code: 'QUERY_ERROR' | 'FILE_ERROR' | 'EXPORT_ERROR';
  message: string;
};

export type ExportResult = ExportSuccess | ExportError;

function isError(result: ExportResult): result is ExportError {
  return 'code' in result && 'message' in result;
}

export async function createExportService(databasePath: string = ":memory:", bufferSize: number = 1 << 30) {
  const db = new kuzu.Database(databasePath, bufferSize);
  const conn = new kuzu.Connection(db, 4);
  
  async function exportData(options: ExportOptions): Promise<ExportResult> {
    const { format = 'parquet', query, outputPath } = options;
    const tempPath = `/tmp/export_${Date.now()}.${format}`;
    
    try {
      const exportQuery = `COPY (${query}) TO '${tempPath}'`;
      const queryResult = await conn.query(exportQuery);
      await queryResult.close();
      
      const stats = await kuzu.FS.stat(tempPath);
      const data = await kuzu.FS.readFile(tempPath);
      
      if (outputPath) {
        writeFileSync(outputPath, Buffer.from(data));
      }
      
      await kuzu.FS.unlink(tempPath);
      
      return {
        path: outputPath || tempPath,
        size: stats.size
      };
    } catch (error) {
      return {
        code: 'EXPORT_ERROR',
        message: `[Export Failed] ${error instanceof Error ? error.message : String(error)}`
      };
    }
  }
  
  async function executeQuery(cypherQuery: string) {
    return conn.query(cypherQuery);
  }
  
  async function close() {
    await conn.close();
    await db.close();
    await kuzu.close();
  }
  
  return {
    exportData,
    executeQuery,
    close
  };
}