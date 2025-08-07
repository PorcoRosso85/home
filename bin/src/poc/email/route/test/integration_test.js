#!/usr/bin/env node

/**
 * Integration Test Suite for Email Archive Worker
 * 
 * Tests the complete email archiving workflow:
 * - Email parsing and metadata extraction
 * - S3 storage with MinIO backend
 * - Proper file organization and retrieval
 * - Error handling and edge cases
 */

import { S3Client, PutObjectCommand, GetObjectCommand, ListObjectsV2Command } from "@aws-sdk/client-s3";
import { readFile, readdir } from 'fs/promises';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { strict as assert } from 'assert';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Test configuration - matches setup-minio.sh defaults
const TEST_CONFIG = {
  endpoint: process.env.MINIO_ENDPOINT || "http://localhost:9000",
  accessKeyId: process.env.MINIO_ACCESS_KEY || "minioadmin", 
  secretAccessKey: process.env.MINIO_SECRET_KEY || "minioadmin",
  bucketName: process.env.BUCKET_NAME || "email-archive",
  region: "us-east-1"
};

// Worker module will be loaded dynamically

class IntegrationTestSuite {
  constructor() {
    this.s3Client = new S3Client({
      endpoint: TEST_CONFIG.endpoint,
      region: TEST_CONFIG.region,
      credentials: {
        accessKeyId: TEST_CONFIG.accessKeyId,
        secretAccessKey: TEST_CONFIG.secretAccessKey,
      },
      forcePathStyle: true
    });
    
    this.testResults = [];
    this.fixtures = {};
    this.workerModule = null;
  }

  /**
   * Load the worker module dynamically
   */
  async loadWorkerModule() {
    try {
      this.workerModule = await import('../src/index.js');
      console.log('✅ Worker module loaded successfully');
      console.log('  Default export:', typeof this.workerModule.default);
      console.log('  Email method:', typeof this.workerModule.default?.email);
      console.log('');
    } catch (error) {
      console.error('❌ Failed to load worker module:', error.message);
      throw error;
    }
  }

  /**
   * Load all test email fixtures
   */
  async loadFixtures() {
    console.log('📧 Loading email fixtures...');
    const fixturesDir = join(__dirname, 'fixtures');
    const files = await readdir(fixturesDir);
    
    for (const file of files.filter(f => f.endsWith('.eml'))) {
      const content = await readFile(join(fixturesDir, file), 'utf-8');
      const name = file.replace('.eml', '');
      this.fixtures[name] = content;
      console.log(`  ✓ Loaded ${name}`);
    }
    
    console.log(`📧 Loaded ${Object.keys(this.fixtures).length} email fixtures\n`);
  }

  /**
   * Mock email message for testing worker functions
   */
  createMockMessage(rawEmail, from = 'test@example.com', to = ['recipient@example.com']) {
    const headers = new Map();
    
    // Extract headers from raw email
    const lines = rawEmail.split('\n');
    for (const line of lines) {
      if (line.trim() === '') break; // End of headers
      const match = line.match(/^([^:]+):\s*(.+)$/);
      if (match) {
        headers.set(match[1].toLowerCase(), match[2].trim());
      }
    }
    
    return {
      from,
      to,
      headers,
      raw: async () => new TextEncoder().encode(rawEmail)
    };
  }

  /**
   * Create mock environment for worker
   */
  createMockEnv() {
    return {
      MINIO_ENDPOINT: TEST_CONFIG.endpoint,
      MINIO_ACCESS_KEY: TEST_CONFIG.accessKeyId,
      MINIO_SECRET_KEY: TEST_CONFIG.secretAccessKey,
      BUCKET_NAME: TEST_CONFIG.bucketName
    };
  }

  /**
   * Test helper: Check if MinIO is accessible
   */
  async checkMinIOConnection() {
    console.log('🔍 Checking MinIO connection...');
    try {
      const command = new ListObjectsV2Command({
        Bucket: TEST_CONFIG.bucketName,
        MaxKeys: 1
      });
      
      await this.s3Client.send(command);
      console.log('✅ MinIO connection successful\n');
      return true;
    } catch (error) {
      console.error('❌ MinIO connection failed:', error.message);
      console.error('   Make sure MinIO is running: ./setup-minio.sh --keep-running\n');
      return false;
    }
  }

  /**
   * Test: Basic email archiving workflow
   */
  async testBasicEmailArchiving() {
    console.log('🧪 Testing basic email archiving...');
    
    if (!this.workerModule) {
      throw new Error('Worker module not loaded');
    }
    
    const rawEmail = this.fixtures.simple_text;
    const mockMessage = this.createMockMessage(rawEmail);
    const mockEnv = this.createMockEnv();
    
    try {
      // Call the worker's email handler
      const response = await this.workerModule.default.email(mockMessage, mockEnv, {});
      
      assert.equal(response.status, 200, 'Expected successful response');
      assert(response.headers.get('Content-Type').includes('text/plain'), 'Expected text response');
      
      const responseText = await response.text();
      assert(responseText.includes('archived successfully'), 'Expected success message');
      
      console.log('  ✅ Worker processed email successfully');
      
      // Verify files were stored in S3
      const messageId = 'simple-text-123@example.com'; // Based on fixture message ID (the worker cleans it to simple-text-123@example.com)
      const today = new Date();
      const storagePrefix = `emails/${today.getFullYear()}/${String(today.getMonth() + 1).padStart(2, '0')}/${String(today.getDate()).padStart(2, '0')}`;
      
      // Check for .eml file
      const emlKey = `${storagePrefix}/${messageId}.eml`;
      try {
        const emlCommand = new GetObjectCommand({
          Bucket: TEST_CONFIG.bucketName,
          Key: emlKey
        });
        const emlResult = await this.s3Client.send(emlCommand);
        console.log('  ✅ EML file stored successfully');
        
        // Verify content
        const storedContent = await this.streamToString(emlResult.Body);
        assert(storedContent.includes('Simple Text Email'), 'EML content should match original');
      } catch (error) {
        // Try to find any file with similar pattern
        const listCommand = new ListObjectsV2Command({
          Bucket: TEST_CONFIG.bucketName,
          Prefix: storagePrefix
        });
        const listResult = await this.s3Client.send(listCommand);
        console.log('  📋 Available files:', listResult.Contents?.map(obj => obj.Key) || []);
        throw new Error(`EML file not found at ${emlKey}: ${error.message}`);
      }
      
      // Check for .json metadata file
      const jsonKey = `${storagePrefix}/${messageId}.json`;
      try {
        const jsonCommand = new GetObjectCommand({
          Bucket: TEST_CONFIG.bucketName,
          Key: jsonKey
        });
        const jsonResult = await this.s3Client.send(jsonCommand);
        console.log('  ✅ JSON metadata stored successfully');
        
        // Verify metadata structure
        const metadata = JSON.parse(await this.streamToString(jsonResult.Body));
        assert(metadata.messageId, 'Metadata should have messageId');
        assert(metadata.from, 'Metadata should have from');
        assert(metadata.subject, 'Metadata should have subject');
        assert(metadata.receivedAt, 'Metadata should have receivedAt');
        console.log('  ✅ Metadata structure is valid');
      } catch (error) {
        throw new Error(`JSON metadata not found at ${jsonKey}: ${error.message}`);
      }
      
      this.testResults.push({ test: 'Basic Email Archiving', status: 'PASS' });
      console.log('✅ Basic email archiving test passed\n');
      
    } catch (error) {
      this.testResults.push({ test: 'Basic Email Archiving', status: 'FAIL', error: error.message });
      console.error('❌ Basic email archiving test failed:', error.message);
      throw error;
    }
  }

  /**
   * Test: HTML email with attachment
   */
  async testHTMLEmailWithAttachment() {
    console.log('🧪 Testing HTML email with attachment...');
    
    const rawEmail = this.fixtures.html_with_attachment;
    const mockMessage = this.createMockMessage(rawEmail);
    const mockEnv = this.createMockEnv();
    
    try {
      const response = await this.workerModule.default.email(mockMessage, mockEnv, {});
      assert.equal(response.status, 200, 'Expected successful response');
      
      console.log('  ✅ HTML email with attachment processed successfully');
      
      // Verify metadata extraction detected the attachment
      const today = new Date();
      const storagePrefix = `emails/${today.getFullYear()}/${String(today.getMonth() + 1).padStart(2, '0')}/${String(today.getDate()).padStart(2, '0')}`;
      
      // Find the JSON file for this email
      const listCommand = new ListObjectsV2Command({
        Bucket: TEST_CONFIG.bucketName,
        Prefix: storagePrefix,
        MaxKeys: 100
      });
      const listResult = await this.s3Client.send(listCommand);
      
      const jsonFiles = (listResult.Contents || []).filter(obj => obj.Key.endsWith('.json'));
      const htmlEmailJson = jsonFiles.find(obj => obj.Key.includes('html-attachment'));
      
      if (htmlEmailJson) {
        const getCommand = new GetObjectCommand({
          Bucket: TEST_CONFIG.bucketName,
          Key: htmlEmailJson.Key
        });
        const result = await this.s3Client.send(getCommand);
        const metadata = JSON.parse(await this.streamToString(result.Body));
        
        assert(metadata.isMultipart, 'Should detect multipart email');
        assert(metadata.attachments && metadata.attachments.length > 0, 'Should detect attachments');
        console.log('  ✅ Attachment detection works correctly');
      }
      
      this.testResults.push({ test: 'HTML Email with Attachment', status: 'PASS' });
      console.log('✅ HTML email with attachment test passed\n');
      
    } catch (error) {
      this.testResults.push({ test: 'HTML Email with Attachment', status: 'FAIL', error: error.message });
      console.error('❌ HTML email with attachment test failed:', error.message);
      throw error;
    }
  }

  /**
   * Test: Malformed email handling
   */
  async testMalformedEmailHandling() {
    console.log('🧪 Testing malformed email handling...');
    
    const rawEmail = this.fixtures.malformed;
    const mockMessage = this.createMockMessage(rawEmail);
    const mockEnv = this.createMockEnv();
    
    try {
      const response = await this.workerModule.default.email(mockMessage, mockEnv, {});
      
      // Should handle gracefully without throwing
      assert(response.status === 200 || response.status === 500, 'Should return valid HTTP status');
      
      console.log('  ✅ Malformed email handled gracefully');
      
      this.testResults.push({ test: 'Malformed Email Handling', status: 'PASS' });
      console.log('✅ Malformed email handling test passed\n');
      
    } catch (error) {
      this.testResults.push({ test: 'Malformed Email Handling', status: 'FAIL', error: error.message });
      console.error('❌ Malformed email handling test failed:', error.message);
    }
  }

  /**
   * Test: Storage key generation and organization
   */
  async testStorageKeyGeneration() {
    console.log('🧪 Testing storage key generation...');
    
    try {
      // Process multiple emails and verify they're organized correctly
      const emails = [
        { name: 'simple_text', fixture: this.fixtures.simple_text },
        { name: 'multipart', fixture: this.fixtures.multipart }
      ];
      
      for (const email of emails) {
        const mockMessage = this.createMockMessage(email.fixture);
        const mockEnv = this.createMockEnv();
        await this.workerModule.default.email(mockMessage, mockEnv, {});
      }
      
      // Verify hierarchical organization
      const listCommand = new ListObjectsV2Command({
        Bucket: TEST_CONFIG.bucketName,
        Prefix: 'emails/',
        MaxKeys: 100
      });
      const listResult = await this.s3Client.send(listCommand);
      
      const objects = listResult.Contents || [];
      assert(objects.length > 0, 'Should have stored objects');
      
      // Check hierarchical structure: emails/YYYY/MM/DD/messageId.ext
      const pathPattern = /^emails\/\d{4}\/\d{2}\/\d{2}\/[^\/]+\.(eml|json)$/;
      const validPaths = objects.filter(obj => pathPattern.test(obj.Key));
      
      assert(validPaths.length > 0, 'Should have objects with correct path structure');
      console.log(`  ✅ Found ${validPaths.length} objects with correct hierarchical structure`);
      
      this.testResults.push({ test: 'Storage Key Generation', status: 'PASS' });
      console.log('✅ Storage key generation test passed\n');
      
    } catch (error) {
      this.testResults.push({ test: 'Storage Key Generation', status: 'FAIL', error: error.message });
      console.error('❌ Storage key generation test failed:', error.message);
    }
  }

  /**
   * Test: Performance with multiple concurrent emails  
   */
  async testConcurrentProcessing() {
    console.log('🧪 Testing concurrent email processing...');
    
    try {
      const startTime = Date.now();
      const concurrentTasks = [];
      
      // Process multiple emails concurrently
      for (let i = 0; i < 5; i++) {
        const rawEmail = this.fixtures.simple_text.replace(
          'Message-ID: <simple-text-123@example.com>',
          `Message-ID: <concurrent-test-${i}@example.com>`
        );
        
        const mockMessage = this.createMockMessage(rawEmail);
        const mockEnv = this.createMockEnv();
        
        concurrentTasks.push(this.workerModule.default.email(mockMessage, mockEnv, {}));
      }
      
      const results = await Promise.all(concurrentTasks);
      const endTime = Date.now();
      
      // All should succeed
      results.forEach((response, index) => {
        assert.equal(response.status, 200, `Concurrent task ${index} should succeed`);
      });
      
      const processingTime = endTime - startTime;
      console.log(`  ✅ Processed 5 emails concurrently in ${processingTime}ms`);
      assert(processingTime < 10000, 'Should complete within reasonable time');
      
      this.testResults.push({ test: 'Concurrent Processing', status: 'PASS' });
      console.log('✅ Concurrent processing test passed\n');
      
    } catch (error) {
      this.testResults.push({ test: 'Concurrent Processing', status: 'FAIL', error: error.message });
      console.error('❌ Concurrent processing test failed:', error.message);
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
   * Print test results summary
   */
  printResults() {
    console.log('\n📊 TEST RESULTS SUMMARY');
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
    console.log(`Total Tests: ${this.testResults.length}`);
    console.log(`✅ Passed: ${passed}`);
    console.log(`❌ Failed: ${failed}`);
    
    if (failed === 0) {
      console.log('\n🎉 All integration tests passed!');
      return 0;
    } else {
      console.log('\n⚠️  Some tests failed. Check the output above for details.');
      return 1;
    }
  }

  /**
   * Run all integration tests
   */
  async run() {
    console.log('🚀 Starting Email Archive Integration Tests\n');
    
    try {
      // Check prerequisites
      if (!(await this.checkMinIOConnection())) {
        return 1;
      }
      
      // Load worker module
      await this.loadWorkerModule();
      
      // Load test fixtures
      await this.loadFixtures();
      
      // Run all tests
      await this.testBasicEmailArchiving();
      await this.testHTMLEmailWithAttachment();
      await this.testMalformedEmailHandling();
      await this.testStorageKeyGeneration();
      await this.testConcurrentProcessing();
      
      return this.printResults();
      
    } catch (error) {
      console.error('\n💥 Test suite failed with critical error:', error.message);
      return 1;
    }
  }
}

// Run tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const testSuite = new IntegrationTestSuite();
  const exitCode = await testSuite.run();
  process.exit(exitCode);
}

export default IntegrationTestSuite;