#!/usr/bin/env node

/**
 * End-to-End Test Suite for Email Archive Worker
 * 
 * Tests the complete email workflow from end-to-end:
 * - Worker deployment simulation
 * - Real email processing pipeline
 * - Full storage verification
 * - Performance benchmarks
 */

import { S3Client, ListObjectsV2Command, GetObjectCommand, DeleteObjectCommand } from "@aws-sdk/client-s3";
import { readFile, readdir } from 'fs/promises';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { strict as assert } from 'assert';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// E2E Test configuration
const E2E_CONFIG = {
  endpoint: process.env.MINIO_ENDPOINT || "http://localhost:9000",
  accessKeyId: process.env.MINIO_ACCESS_KEY || "minioadmin", 
  secretAccessKey: process.env.MINIO_SECRET_KEY || "minioadmin",
  bucketName: process.env.BUCKET_NAME || "email-archive",
  region: "us-east-1"
};

class E2ETestSuite {
  constructor() {
    this.s3Client = new S3Client({
      endpoint: E2E_CONFIG.endpoint,
      region: E2E_CONFIG.region,
      credentials: {
        accessKeyId: E2E_CONFIG.accessKeyId,
        secretAccessKey: E2E_CONFIG.secretAccessKey,
      },
      forcePathStyle: true
    });
    
    this.testResults = [];
    this.fixtures = {};
    this.workerModule = null;
    this.testPrefix = `e2e-test-${Date.now()}`;
  }

  /**
   * Load the worker module and fixtures
   */
  async setup() {
    console.log('🚀 Setting up E2E Test Environment\n');
    
    // Load worker module
    try {
      this.workerModule = await import('../../src/index.js');
      console.log('✅ Worker module loaded');
    } catch (error) {
      console.error('❌ Failed to load worker module:', error.message);
      throw error;
    }
    
    // Load fixtures
    console.log('📧 Loading email fixtures...');
    const fixturesDir = join(__dirname, '../fixtures');
    const files = await readdir(fixturesDir);
    
    for (const file of files.filter(f => f.endsWith('.eml'))) {
      const content = await readFile(join(fixturesDir, file), 'utf-8');
      const name = file.replace('.eml', '');
      this.fixtures[name] = content;
    }
    
    console.log(`✅ Loaded ${Object.keys(this.fixtures).length} fixtures\n`);
  }

  /**
   * Create mock email message for E2E testing
   */
  createMockMessage(rawEmail, from = 'e2e-test@example.com', to = ['recipient@example.com']) {
    const headers = new Map();
    
    // Extract headers from raw email
    const lines = rawEmail.split('\n');
    for (const line of lines) {
      if (line.trim() === '') break;
      const match = line.match(/^([^:]+):\s*(.+)$/);
      if (match) {
        headers.set(match[1].toLowerCase(), match[2].trim());
      }
    }
    
    // Override Message-ID for E2E testing
    const messageId = `${this.testPrefix}-${Date.now()}@example.com`;
    headers.set('message-id', `<${messageId}>`);
    
    return {
      from,
      to,
      headers,
      raw: async () => new TextEncoder().encode(rawEmail.replace(
        /Message-ID: <[^>]+>/,
        `Message-ID: <${messageId}>`
      ))
    };
  }

  /**
   * Create mock environment
   */
  createMockEnv() {
    return {
      MINIO_ENDPOINT: E2E_CONFIG.endpoint,
      MINIO_ACCESS_KEY: E2E_CONFIG.accessKeyId,
      MINIO_SECRET_KEY: E2E_CONFIG.secretAccessKey,
      BUCKET_NAME: E2E_CONFIG.bucketName
    };
  }

  /**
   * Test: Full email processing pipeline
   */
  async testEmailProcessingPipeline() {
    console.log('🧪 Testing full email processing pipeline...');
    
    const testEmails = [
      { name: 'simple_text', fixture: this.fixtures.simple_text },
      { name: 'multipart', fixture: this.fixtures.multipart },
      { name: 'html_with_attachment', fixture: this.fixtures.html_with_attachment }
    ];
    
    const processedEmails = [];
    
    try {
      for (const email of testEmails) {
        console.log(`  Processing ${email.name}...`);
        
        const mockMessage = this.createMockMessage(email.fixture);
        const mockEnv = this.createMockEnv();
        
        const startTime = Date.now();
        const response = await this.workerModule.default.email(mockMessage, mockEnv, {});
        const processingTime = Date.now() - startTime;
        
        assert.equal(response.status, 200, `${email.name} should process successfully`);
        
        const responseText = await response.text();
        assert(responseText.includes('archived successfully'), `${email.name} should return success message`);
        
        processedEmails.push({
          name: email.name,
          messageId: mockMessage.headers.get('message-id').replace(/[<>]/g, ''),
          processingTime
        });
        
        console.log(`    ✅ ${email.name} processed in ${processingTime}ms`);
      }
      
      console.log('  ✅ All emails processed successfully');
      
      // Verify all emails are stored
      await this.verifyStoredEmails(processedEmails);
      
      this.testResults.push({ test: 'Email Processing Pipeline', status: 'PASS' });
      console.log('✅ Email processing pipeline test passed\n');
      
    } catch (error) {
      this.testResults.push({ test: 'Email Processing Pipeline', status: 'FAIL', error: error.message });
      console.error('❌ Email processing pipeline test failed:', error.message);
      throw error;
    }
  }

  /**
   * Verify emails are stored correctly in S3
   */
  async verifyStoredEmails(processedEmails) {
    console.log('  🔍 Verifying stored emails...');
    
    const today = new Date();
    const storagePrefix = `emails/${today.getFullYear()}/${String(today.getMonth() + 1).padStart(2, '0')}/${String(today.getDate()).padStart(2, '0')}`;
    
    for (const email of processedEmails) {
      const cleanMessageId = email.messageId.replace(/[<>@]/g, '').replace(/\./g, '-');
      
      // Check EML file
      const emlKey = `${storagePrefix}/${cleanMessageId}.eml`;
      try {
        const emlCommand = new GetObjectCommand({
          Bucket: E2E_CONFIG.bucketName,
          Key: emlKey
        });
        await this.s3Client.send(emlCommand);
        console.log(`    ✅ EML file found: ${emlKey}`);
      } catch (error) {
        throw new Error(`EML file not found for ${email.name}: ${emlKey}`);
      }
      
      // Check JSON metadata
      const jsonKey = `${storagePrefix}/${cleanMessageId}.json`;
      try {
        const jsonCommand = new GetObjectCommand({
          Bucket: E2E_CONFIG.bucketName,
          Key: jsonKey
        });
        const jsonResult = await this.s3Client.send(jsonCommand);
        
        const metadata = JSON.parse(await this.streamToString(jsonResult.Body));
        assert(metadata.messageId, 'Metadata should have messageId');
        assert(metadata.from, 'Metadata should have from');
        assert(metadata.subject, 'Metadata should have subject');
        assert(metadata.receivedAt, 'Metadata should have receivedAt');
        
        console.log(`    ✅ JSON metadata found: ${jsonKey}`);
      } catch (error) {
        throw new Error(`JSON metadata not found for ${email.name}: ${jsonKey}`);
      }
    }
  }

  /**
   * Test: Performance benchmark
   */
  async testPerformanceBenchmark() {
    console.log('🧪 Testing performance benchmark...');
    
    const iterations = 10;
    const processingTimes = [];
    
    try {
      console.log(`  Running ${iterations} iterations...`);
      
      for (let i = 0; i < iterations; i++) {
        const rawEmail = this.fixtures.simple_text.replace(
          'Message-ID: <simple-text-123@example.com>',
          `Message-ID: <perf-test-${i}-${Date.now()}@example.com>`
        );
        
        const mockMessage = this.createMockMessage(rawEmail);
        const mockEnv = this.createMockEnv();
        
        const startTime = Date.now();
        const response = await this.workerModule.default.email(mockMessage, mockEnv, {});
        const processingTime = Date.now() - startTime;
        
        assert.equal(response.status, 200, `Iteration ${i} should succeed`);
        processingTimes.push(processingTime);
        
        if (i % 2 === 0) {
          process.stdout.write('.');
        }
      }
      
      console.log('');
      
      // Calculate performance metrics
      const avgTime = processingTimes.reduce((a, b) => a + b, 0) / processingTimes.length;
      const maxTime = Math.max(...processingTimes);
      const minTime = Math.min(...processingTimes);
      
      console.log(`  📊 Performance Results:`);
      console.log(`    Average: ${avgTime.toFixed(2)}ms`);
      console.log(`    Min: ${minTime}ms`);
      console.log(`    Max: ${maxTime}ms`);
      
      // Performance assertions
      assert(avgTime < 2000, `Average processing time (${avgTime}ms) should be under 2 seconds`);
      assert(maxTime < 5000, `Max processing time (${maxTime}ms) should be under 5 seconds`);
      
      this.testResults.push({ test: 'Performance Benchmark', status: 'PASS' });
      console.log('✅ Performance benchmark test passed\n');
      
    } catch (error) {
      this.testResults.push({ test: 'Performance Benchmark', status: 'FAIL', error: error.message });
      console.error('❌ Performance benchmark test failed:', error.message);
    }
  }

  /**
   * Test: Storage cleanup and organization
   */
  async testStorageOrganization() {
    console.log('🧪 Testing storage organization...');
    
    try {
      // List all objects with our test prefix
      const listCommand = new ListObjectsV2Command({
        Bucket: E2E_CONFIG.bucketName,
        Prefix: 'emails/',
        MaxKeys: 1000
      });
      
      const result = await this.s3Client.send(listCommand);
      const objects = result.Contents || [];
      
      console.log(`  📋 Found ${objects.length} stored objects`);
      
      // Verify hierarchical structure
      const pathPattern = /^emails\/\d{4}\/\d{2}\/\d{2}\/[^\/]+\.(eml|json)$/;
      const validObjects = objects.filter(obj => pathPattern.test(obj.Key));
      
      console.log(`  ✅ ${validObjects.length} objects follow correct naming convention`);
      assert(validObjects.length > 0, 'Should have objects with correct structure');
      
      // Verify paired files (each email should have both .eml and .json)
      const emlFiles = validObjects.filter(obj => obj.Key.endsWith('.eml'));
      const jsonFiles = validObjects.filter(obj => obj.Key.endsWith('.json'));
      
      console.log(`  📧 EML files: ${emlFiles.length}`);
      console.log(`  📄 JSON files: ${jsonFiles.length}`);
      
      // Check for orphaned files
      const orphanedFiles = [];
      for (const eml of emlFiles) {
        const expectedJson = eml.Key.replace('.eml', '.json');
        if (!jsonFiles.find(json => json.Key === expectedJson)) {
          orphanedFiles.push(`Missing JSON for: ${eml.Key}`);
        }
      }
      
      for (const json of jsonFiles) {
        const expectedEml = json.Key.replace('.json', '.eml');
        if (!emlFiles.find(eml => eml.Key === expectedEml)) {
          orphanedFiles.push(`Missing EML for: ${json.Key}`);
        }
      }
      
      if (orphanedFiles.length > 0) {
        console.warn('  ⚠️ Orphaned files detected:', orphanedFiles);
      } else {
        console.log('  ✅ All files properly paired');
      }
      
      this.testResults.push({ test: 'Storage Organization', status: 'PASS' });
      console.log('✅ Storage organization test passed\n');
      
    } catch (error) {
      this.testResults.push({ test: 'Storage Organization', status: 'FAIL', error: error.message });
      console.error('❌ Storage organization test failed:', error.message);
    }
  }

  /**
   * Helper: Convert stream to string
   */
  async streamToString(stream) {
    const chunks = [];
    for await (const chunk of stream) {
      chunks.push(chunk);
    }
    return Buffer.concat(chunks).toString('utf-8');
  }

  /**
   * Cleanup test data
   */
  async cleanup() {
    console.log('🧹 Cleaning up test data...');
    
    try {
      // List and delete all test objects
      const listCommand = new ListObjectsV2Command({
        Bucket: E2E_CONFIG.bucketName,
        Prefix: 'emails/',
        MaxKeys: 1000
      });
      
      const result = await this.s3Client.send(listCommand);
      const objects = result.Contents || [];
      
      // Filter to only test objects created by this run
      const testObjects = objects.filter(obj => 
        obj.Key.includes(this.testPrefix) || 
        obj.Key.includes('e2e-test') ||
        obj.Key.includes('perf-test')
      );
      
      if (testObjects.length > 0) {
        console.log(`  🗑️ Deleting ${testObjects.length} test objects...`);
        
        for (const obj of testObjects) {
          const deleteCommand = new DeleteObjectCommand({
            Bucket: E2E_CONFIG.bucketName,
            Key: obj.Key
          });
          await this.s3Client.send(deleteCommand);
        }
        
        console.log('  ✅ Test data cleaned up');
      } else {
        console.log('  ℹ️ No test data to clean up');
      }
      
    } catch (error) {
      console.warn('  ⚠️ Cleanup failed:', error.message);
    }
  }

  /**
   * Print test results summary
   */
  printResults() {
    console.log('\n📊 E2E TEST RESULTS SUMMARY');
    console.log('='.repeat(50));
    
    let passed = 0;
    let failed = 0;
    
    this.testResults.forEach(result => {
      const status = result.status === 'PASS' ? '✅' : '❌';
      console.log(`${status} ${result.test}`);
      if (result.error) {
        console.log(`    Error: ${result.error}`);
      }
      
      if (result.status === 'PASS') passed++;
      else failed++;
    });
    
    console.log('='.repeat(50));
    console.log(`Total E2E Tests: ${this.testResults.length}`);
    console.log(`✅ Passed: ${passed}`);
    console.log(`❌ Failed: ${failed}`);
    
    if (failed === 0) {
      console.log('\n🎉 All E2E tests passed!');
      return 0;
    } else {
      console.log('\n⚠️ Some E2E tests failed. Check the output above for details.');
      return 1;
    }
  }

  /**
   * Run all E2E tests
   */
  async run() {
    console.log('🚀 Starting End-to-End Test Suite\n');
    
    try {
      await this.setup();
      
      // Run E2E tests
      await this.testEmailProcessingPipeline();
      await this.testPerformanceBenchmark();
      await this.testStorageOrganization();
      
      return this.printResults();
      
    } catch (error) {
      console.error('\n💥 E2E test suite failed with critical error:', error.message);
      return 1;
    } finally {
      // Always cleanup
      await this.cleanup();
    }
  }
}

// Run E2E tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const testSuite = new E2ETestSuite();
  const exitCode = await testSuite.run();
  process.exit(exitCode);
}

export default E2ETestSuite;