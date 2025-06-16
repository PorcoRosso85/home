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

test('KuzuDB Export - CSV format', { timeout: 30000 }, async () => {
  const service = await createExportService();
  
  try {
    let result = await service.executeQuery("CREATE NODE TABLE CSVTest(value INT64, PRIMARY KEY(value))");
    await result.close();
    
    result = await service.executeQuery("UNWIND range(1, 5) AS i CREATE (:CSVTest {value: i})");
    await result.close();
    
    const outputPath = './test_export.csv';
    const exportResult = await service.exportData({
      query: "MATCH (n:CSVTest) RETURN n.value ORDER BY n.value",
      format: 'csv',
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

test('KuzuDB Export - Error handling', { timeout: 10000 }, async () => {
  const service = await createExportService();
  
  try {
    const exportResult = await service.exportData({
      query: "MATCH (n:NonExistent) RETURN n",
      format: 'parquet'
    });
    
    assert.ok('code' in exportResult);
    assert.equal(exportResult.code, 'EXPORT_ERROR');
    assert.ok(exportResult.message.includes('[Export Failed]'));
  } finally {
    await service.close();
  }
});