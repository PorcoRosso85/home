// Complex TypeScript Type Patterns
// 実務で求められる高度な型チェックパターン

// ======================================
// 1. Generic Constraints - ジェネリクス制約
// ======================================
type Serializable = {
  toJSON(): string;
};

function serialize<T extends Serializable>(obj: T): string {
  return obj.toJSON();
}

// エラー: number型はSerializableを満たさない
// serialize(42);

// ======================================
// 2. Conditional Types - 条件型
// ======================================
type IsString<T> = T extends string ? true : false;
type Result1 = IsString<"hello">; // true
type Result2 = IsString<42>; // false

// より複雑な条件型
type UnwrapPromise<T> = T extends Promise<infer U> ? U : T;
type Unwrapped1 = UnwrapPromise<Promise<string>>; // string
type Unwrapped2 = UnwrapPromise<number>; // number

// ======================================
// 3. Type Guards & Narrowing - 型ガードとナローイング
// ======================================
function isString(value: unknown): value is string {
  return typeof value === 'string';
}

function processValue(value: string | number) {
  if (isString(value)) {
    // ここでvalueはstring型として扱われる
    console.log(value.toUpperCase());
  } else {
    // ここでvalueはnumber型として扱われる
    console.log(value.toFixed(2));
  }
}

// ======================================
// 4. Mapped Types - マップ型
// ======================================
type ReadonlyDeep<T> = {
  readonly [P in keyof T]: T[P] extends object ? ReadonlyDeep<T[P]> : T[P];
};

type MutableUser = {
  name: string;
  address: {
    city: string;
    zip: number;
  };
};

type ImmutableUser = ReadonlyDeep<MutableUser>;
// エラー: readonlyプロパティへの代入
// const user: ImmutableUser = { name: "Alice", address: { city: "Tokyo", zip: 100 } };
// user.address.city = "Osaka";

// ======================================
// 5. Recursive Types - 再帰的型定義
// ======================================
type JSONValue = 
  | string
  | number
  | boolean
  | null
  | JSONObject
  | JSONArray;

type JSONObject = {
  [key: string]: JSONValue;
};

type JSONArray = JSONValue[];

// 正しい使用例
const validJSON: JSONValue = {
  name: "test",
  values: [1, 2, { nested: true }],
  metadata: null
};

// ======================================
// 6. Higher-Order Function Types - 高階関数の型
// ======================================
type Decorator<T> = (target: T) => T;

function memoize<T extends (...args: any[]) => any>(fn: T): T {
  const cache = new Map();
  return ((...args: Parameters<T>) => {
    const key = JSON.stringify(args);
    if (!cache.has(key)) {
      cache.set(key, fn(...args));
    }
    return cache.get(key);
  }) as T;
}

// ======================================
// 7. Exhaustive Check - Union型の網羅性チェック
// ======================================
type Status = 'pending' | 'success' | 'error' | 'cancelled';

function handleStatus(status: Status): string {
  switch (status) {
    case 'pending':
      return 'Processing...';
    case 'success':
      return 'Completed!';
    case 'error':
      return 'Failed!';
    case 'cancelled':
      return 'Cancelled!';
    default:
      // このコードに到達した場合、全てのケースが処理されていない
      const _exhaustive: never = status;
      return _exhaustive;
  }
}

// ======================================
// 8. Template Literal Types - テンプレートリテラル型
// ======================================
type EventName = 'click' | 'focus' | 'blur';
type EventHandler = `on${Capitalize<EventName>}`;
// 結果: "onClick" | "onFocus" | "onBlur"

// エラー: 無効なイベント名
// const handler: EventHandler = "onHover";

// ======================================
// 9. Complex Intersection Types - 複雑な交差型
// ======================================
type Timestamped = {
  createdAt: Date;
  updatedAt: Date;
};

type Identifiable = {
  id: string;
};

type User = {
  name: string;
  email: string;
};

type CompleteUser = User & Timestamped & Identifiable;

// 全てのプロパティが必要
const validUser: CompleteUser = {
  id: "123",
  name: "Alice",
  email: "alice@example.com",
  createdAt: new Date(),
  updatedAt: new Date()
};

// エラー: idプロパティが不足
// const invalidUser: CompleteUser = {
//   name: "Bob",
//   email: "bob@example.com",
//   createdAt: new Date(),
//   updatedAt: new Date()
// };

// ======================================
// 10. Async Type Safety - 非同期処理の型安全性
// ======================================
async function fetchUser(id: string): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  return response.json();
}

async function processUsers(ids: string[]): Promise<User[]> {
  // Promise.allの型推論
  const users = await Promise.all(ids.map(id => fetchUser(id)));
  return users; // User[]型として正しく推論される
}

// エラー例: 誤った型の使用
async function incorrectUsage() {
  const users = await processUsers(["1", "2"]);
  // エラー: User[]にnumber型のメソッドは存在しない
  // users.toFixed(2);
}