#!/usr/bin/env bun
import { Level3Glue, GoProducerContract, BunConsumerContract } from './src/contracts/level3-contract';

console.log('=== Contract Validation Test ===\n');

const glue = new Level3Glue();

// Test 1: Valid compatibility
console.log('Test 1: Valid producer-consumer compatibility');
const result1 = glue.validateCompatibility(GoProducerContract, BunConsumerContract);
console.log('Result:', result1);
console.log('Expected: { valid: true }\n');

// Test 2: Invalid - missing command
console.log('Test 2: Invalid - consumer requires non-existent command');
const invalidConsumer = {
  ...BunConsumerContract,
  commands: {
    missing: {
      command: 'non-existent-command',
      version: '1.0.0',
      capabilities: ['unknown']
    }
  }
};
const result2 = glue.validateCompatibility(GoProducerContract, invalidConsumer);
console.log('Result:', result2);
console.log('Expected: Error about missing command\n');

// Test 3: Invalid - not path-managed
console.log('Test 3: Invalid - producer not path-managed');
const invalidProducer = {
  ...GoProducerContract,
  capabilities: ['pure-contract', 'data-transformer'] // removed 'path-managed'
};
const result3 = glue.validateCompatibility(invalidProducer, BunConsumerContract);
console.log('Result:', result3);
console.log('Expected: Error about path-managed requirement\n');

console.log('=== All tests completed ===');