/**
 * 型安全性検証用TypeScriptサンプル
 * 統一規約に基づく実装での型チェック動作確認
 */

// 1. 基本的な型定義
function addNumbers(a: number, b: number): number {
  return a + b;
}

// 2. インターフェースによる型定義
interface Person {
  name: string;
  age: number;
  email?: string;
}

// 3. 型ガードによる実行時チェック
function isPerson(obj: unknown): obj is Person {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'name' in obj &&
    'age' in obj &&
    typeof (obj as Person).name === 'string' &&
    typeof (obj as Person).age === 'number'
  );
}

// 4. ジェネリック型
class Repository<T> {
  private items: Map<string, T> = new Map();

  add(key: string, value: T): void {
    this.items.set(key, value);
  }

  get(key: string): T | undefined {
    return this.items.get(key);
  }
}

// 5. ユニオン型と型の絞り込み
type Result<T> = { success: true; data: T } | { success: false; error: string };

function processData(input: string | number): Result<string> {
  if (typeof input === 'string') {
    return { success: true, data: input.toUpperCase() };
  } else {
    return { success: true, data: input.toString() };
  }
}

// 6. 型エラーを含むコード（TypeScriptコンパイラが検出すべき）
function problematicFunction() {
  // これらはコンパイルエラーになるべき
  const result = addNumbers("1", "2"); // Error: Argument of type 'string' is not assignable to parameter of type 'number'
  const person: Person = { name: 123, age: "twenty" }; // Error: Type 'number' is not assignable to type 'string'
  return result;
}

// 7. strictNullChecksの確認
function handleNull(value: string | null): string {
  // strictNullChecksが有効な場合、nullチェックが必要
  if (value === null) {
    return "default";
  }
  return value.toUpperCase(); // nullの可能性を排除済み
}

// 使用例
if (import.meta.main) {
  console.log(addNumbers(1, 2));
  
  const person: Person = { name: "Alice", age: 30 };
  console.log(person);
  
  const repo = new Repository<Person>();
  repo.add("alice", person);
  
  const result = processData("hello");
  if (result.success) {
    console.log(result.data);
  }
}