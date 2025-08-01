# Bun版 多段階Vesselパターン集

## 1. スクリプト生成器パターン

### script_generator.ts
```typescript
#!/usr/bin/env bun
// 入力を元にスクリプトを生成する器

const input = await Bun.stdin.text();
const data = JSON.parse(input);

// 入力データからスクリプトを生成
const script = `
  const users = ${JSON.stringify(data.users)};
  const filtered = users.filter(u => u.age > ${data.minAge || 18});
  console.log(JSON.stringify(filtered));
`;

console.log(script);
```

### 使用例
```bash
echo '{"users": [{"name":"Alice","age":25}], "minAge": 20}' | \
  bun script_generator.ts | \
  bun vessel.ts
```

## 2. 変換器チェーンパターン

### csv_to_script.ts
```typescript
#!/usr/bin/env bun
// CSVを処理スクリプトに変換

const csv = await Bun.stdin.text();
const lines = csv.trim().split('\n');
const headers = lines[0].split(',');

const script = `
  const data = ${JSON.stringify(lines.slice(1).map(line => {
    const values = line.split(',');
    return Object.fromEntries(headers.map((h, i) => [h, values[i]]));
  }))};
  
  // 集計処理
  const summary = data.reduce((acc, row) => {
    acc.total += parseFloat(row.amount || 0);
    return acc;
  }, {total: 0, count: data.length});
  
  console.log(JSON.stringify(summary));
`;

console.log(script);
```

### 使用例
```bash
cat sales.csv | bun csv_to_script.ts | bun vessel.ts
```

## 3. APIクライアント生成器

### api_vessel_generator.ts
```typescript
#!/usr/bin/env bun
// API呼び出しスクリプトを生成

const config = JSON.parse(await Bun.stdin.text());

const script = `
  const response = await fetch('${config.url}', {
    method: '${config.method || 'GET'}',
    headers: ${JSON.stringify(config.headers || {})},
    ${config.body ? `body: JSON.stringify(${JSON.stringify(config.body)})` : ''}
  });
  
  const data = await response.json();
  
  // カスタム処理
  ${config.transform || 'console.log(JSON.stringify(data))'}
`;

console.log(script);
```

### 使用例
```bash
echo '{"url":"https://api.github.com/users/octocat","transform":"console.log(data.name)"}' | \
  bun api_vessel_generator.ts | \
  bun vessel.ts
```

## 4. 条件付き器パターン

### conditional_vessel.ts
```typescript
#!/usr/bin/env bun
// 条件に応じて異なるスクリプトを生成

const input = await Bun.stdin.text();
const { mode, data } = JSON.parse(input);

let script = '';

switch(mode) {
  case 'filter':
    script = `
      const items = ${JSON.stringify(data)};
      console.log(JSON.stringify(items.filter(x => x.active)));
    `;
    break;
    
  case 'transform':
    script = `
      const items = ${JSON.stringify(data)};
      console.log(JSON.stringify(items.map(x => ({...x, processed: true}))));
    `;
    break;
    
  case 'aggregate':
    script = `
      const items = ${JSON.stringify(data)};
      const sum = items.reduce((acc, x) => acc + x.value, 0);
      console.log(JSON.stringify({total: sum, average: sum/items.length}));
    `;
    break;
}

console.log(script);
```

## 5. テスト生成器パターン

### test_generator_vessel.ts
```typescript
#!/usr/bin/env bun
// 関数定義からテストコードを生成

const funcDef = await Bun.stdin.text();

const script = `
  ${funcDef}
  
  // 自動生成されたテスト
  const testCases = [
    { input: 1, expected: 2 },
    { input: 0, expected: 1 },
    { input: -1, expected: 0 },
  ];
  
  testCases.forEach(({input, expected}, i) => {
    const result = increment(input);
    console.log(\`Test \${i + 1}: \${result === expected ? 'PASS' : 'FAIL'}\`);
  });
`;

console.log(script);
```

### 使用例
```bash
echo 'function increment(x) { return x + 1; }' | \
  bun test_generator_vessel.ts | \
  bun vessel.ts
```

## 6. 並列処理器パターン

### parallel_vessel.ts
```typescript
#!/usr/bin/env bun
// 並列処理スクリプトを生成

const tasks = JSON.parse(await Bun.stdin.text());

const script = `
  const results = await Promise.all([
    ${tasks.map(task => `
      (async () => {
        ${task.code}
      })()`
    ).join(',\n    ')}
  ]);
  
  console.log(JSON.stringify(results));
`;

console.log(script);
```

### 使用例
```bash
echo '[
  {"code": "return await fetch(\"https://api1.com\").then(r => r.json())"},
  {"code": "return await fetch(\"https://api2.com\").then(r => r.json())"}
]' | bun parallel_vessel.ts | bun vessel.ts
```

## まとめ

これらのパターンは「器の器」として機能し、以下の価値を提供：

1. **動的スクリプト生成** - 入力に応じて実行コードを生成
2. **段階的変換** - データ→スクリプト→実行結果
3. **再利用可能な抽象化** - 共通パターンの器化
4. **LLMとの親和性** - 自然言語的な指示から実行可能コードへ