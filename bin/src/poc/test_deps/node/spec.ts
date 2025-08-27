// 仕様定義（構造体として）
export interface FunctionSpec {
  name: string;
  description: string;
  cases: {
    input: any;
    expected: any;
    description: string;
  }[];
}

export const calculatorSpec: FunctionSpec[] = [
  {
    name: 'add',
    description: '2つの数値を加算する',
    cases: [
      { input: [1, 2], expected: 3, description: '正の整数の加算' },
      { input: [0, 0], expected: 0, description: 'ゼロの加算' },
      { input: [-1, 1], expected: 0, description: '正負の数の加算' },
    ]
  },
  {
    name: 'multiply',
    description: '2つの数値を乗算する',
    cases: [
      { input: [2, 3], expected: 6, description: '正の整数の乗算' },
      { input: [0, 5], expected: 0, description: 'ゼロとの乗算' },
      { input: [-2, 3], expected: -6, description: '負の数の乗算' },
    ]
  }
];

// 仕様のメタデータ
export const specMetadata = {
  version: '1.0.0',
  lastUpdated: '2024-01-01',
  dependencies: [],
  category: 'math-operations'
};