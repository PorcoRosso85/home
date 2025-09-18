#!/usr/bin/env bun
/**
 * Internal Test - flake.nixパッケージの契約検証
 * 
 * テスト対象：
 * - flake.nix#producer (lines 53-60): モックProducer実装
 * - flake.nix#consumer (lines 63-69): モックConsumer実装
 * 
 * これらの出力が契約（src/contracts/）に準拠することを検証
 */

import { test, expect } from 'bun:test';
import { spawn } from 'bun';
import { GoProducerContract, BunConsumerContract } from '../src/contracts/command-contract';

// テスト用の入力データ（契約に準拠）
const testInput = {
  items: ['test1', 'test2', 'test3']
};

test('[Producer] flake.nix#producerの出力が契約を守る', async () => {
  // このflakeのproducerパッケージを実行
  // flake.nix:53-60で定義されたモック実装
  const proc = spawn({
    cmd: ['nix', 'run', '.#producer'],
    cwd: '..'  // contract-flake/
  });
  
  const output = await new Response(proc.stdout).text();
  const result = JSON.parse(output);
  
  // 契約で定義された出力形式を検証
  expect(result).toHaveProperty('processed');
  expect(result).toHaveProperty('failed');
  expect(result).toHaveProperty('output');
  expect(typeof result.processed).toBe('number');
  expect(typeof result.failed).toBe('number');
  expect(Array.isArray(result.output)).toBe(true);
});

test('[Consumer] flake.nix#consumerの出力が契約を守る', async () => {
  // このflakeのconsumerパッケージを実行
  // flake.nix:63-69で定義されたモック実装
  const proc = spawn({
    cmd: ['nix', 'run', '.#consumer'],
    stdin: Buffer.from(JSON.stringify(testInput))
  });
  
  const output = await new Response(proc.stdout).text();
  const result = JSON.parse(output);
  
  // Consumer契約の出力を検証
  expect(result).toHaveProperty('summary');
  expect(result).toHaveProperty('details');
  expect(typeof result.summary).toBe('string');
});

test('[Integration] flake.nix#producer→#consumer接続', async () => {
  // 1. flake.nix#producerを実行
  const producer = spawn({
    cmd: ['nix', 'run', '.#producer']
  });
  
  const producerOutput = await new Response(producer.stdout).text();
  
  // 2. Producer出力をflake.nix#consumerに渡す
  const consumer = spawn({
    cmd: ['nix', 'run', '.#consumer'],
    stdin: Buffer.from(producerOutput)
  });
  
  const consumerOutput = await new Response(consumer.stdout).text();
  const finalResult = JSON.parse(consumerOutput);
  
  // 3. 最終結果を検証
  expect(finalResult).toBeDefined();
  expect(finalResult.summary).toContain('processed');
});

// 契約違反を検出するテスト
test('[Negative] 不正な出力形式を検出', async () => {
  // わざと契約違反するモック実装
  const invalidOutput = {
    wrong_field: 'this violates contract'
  };
  
  // 契約検証が失敗することを確認
  expect(() => {
    // GoProducerContractの出力スキーマで検証
    const schema = GoProducerContract.interface.outputs.result;
    schema.parse(invalidOutput);
  }).toThrow();
});

// テスト実行時のメトリクス表示
if (import.meta.main) {
  console.log('🧪 Internal Contract Test');
  console.log('========================');
  console.log('');
  console.log('Testing contract compliance for:');
  console.log('- Producer implementation');
  console.log('- Consumer implementation');
  console.log('- Producer→Consumer integration');
  console.log('');
}