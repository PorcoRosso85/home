import { test } from 'node:test';
import { strict as assert } from 'node:assert';
import { existsSync, unlinkSync } from 'fs';
import { createExportService } from './exportService.ts';

test('KuzuDB Export - Parquet format', { timeout: 30000 }, async () => {
  const service = await createExportService();
  
  try {
    let result = await service.executeQuery("CREATE NODE TABLE TestNode(id INT64, name STRING, PRIMARY KEY(id))");
    await result.close();
    
    result = await service.executeQuery("CREATE (:TestNode {id: 1, name: 'Node1'})");
    await result.close();
    
    result = await service.executeQuery("CREATE (:TestNode {id: 2, name: 'Node2'})");
    await result.close();
    
    const outputPath = './test_export.parquet';
    const exportResult = await service.exportData({
      query: "MATCH (n:TestNode) RETURN n.id, n.name",
      format: 'parquet',
      outputPath
    });
    
    if ('code' in exportResult) {
      assert.fail(`Export failed: ${exportResult.message}`);
    }
    
    assert.equal(exportResult.path, outputPath);
    assert.ok(exportResult.size > 0);
    assert.equal(existsSync(outputPath), true);
    
    if (existsSync(outputPath)) {
      unlinkSync(outputPath);
    }
  } finally {
    await service.close();
  }
});