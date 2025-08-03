// Complex TypeScript Type Patterns - Error Examples
// コメントを外してエラー検出を確認

// ======================================
// 1. Generic Constraints - ジェネリクス制約違反
// ======================================
type Serializable = {
  toJSON(): string;
};

function serialize<T extends Serializable>(obj: T): string {
  return obj.toJSON();
}

// エラー: number型はSerializableを満たさない
serialize(42);

// ======================================
// 2. Conditional Types - 条件型のエラー
// ======================================
type IsString<T> = T extends string ? true : false;
type ErrorCheck: IsString<number> = true; // エラー: falseをtrueに代入

// ======================================
// 3. Type Guards - 誤った型アサーション
// ======================================
function processValue(value: string | number) {
  // エラー: numberの可能性があるのにstring専用メソッドを使用
  console.log(value.toUpperCase());
}

// ======================================
// 4. Mapped Types - readonly違反
// ======================================
type ReadonlyDeep<T> = {
  readonly [P in keyof T]: T[P] extends object ? ReadonlyDeep<T[P]> : T[P];
};

type ImmutableUser = ReadonlyDeep<{
  name: string;
  address: { city: string; zip: number; };
}>;

const user: ImmutableUser = { name: "Alice", address: { city: "Tokyo", zip: 100 } };
user.address.city = "Osaka"; // エラー: readonlyプロパティへの代入

// ======================================
// 5. Recursive Types - 型の不一致
// ======================================
type JSONValue = string | number | boolean | null | JSONObject | JSONArray;
type JSONObject = { [key: string]: JSONValue; };
type JSONArray = JSONValue[];

// エラー: undefined は JSONValue に含まれない
const invalidJSON: JSONValue = { value: undefined };

// ======================================
// 6. Higher-Order Functions - 引数の型不一致
// ======================================
function memoize<T extends (...args: any[]) => any>(fn: T): T {
  return fn; // 簡略化
}

// エラー: 文字列は関数ではない
memoize("not a function");

// ======================================
// 7. Exhaustive Check - 処理漏れ
// ======================================
type Status = 'pending' | 'success' | 'error' | 'cancelled';

function incompleteHandler(status: Status): string {
  switch (status) {
    case 'pending':
      return 'Processing...';
    case 'success':
      return 'Completed!';
    // errorとcancelledの処理が漏れている
    default:
      const _exhaustive: never = status; // エラー: 'error' | 'cancelled' は never に代入できない
      return _exhaustive;
  }
}

// ======================================
// 8. Template Literal Types - 無効なパターン
// ======================================
type EventHandler = `on${Capitalize<'click' | 'focus' | 'blur'>}`;
const handler: EventHandler = "onHover"; // エラー: "onHover"は有効なEventHandlerではない

// ======================================
// 9. Intersection Types - プロパティ不足
// ======================================
type CompleteUser = {
  id: string;
  name: string;
  email: string;
} & {
  createdAt: Date;
  updatedAt: Date;
};

// エラー: idプロパティが不足
const invalidUser: CompleteUser = {
  name: "Bob",
  email: "bob@example.com",
  createdAt: new Date(),
  updatedAt: new Date()
};

// ======================================
// 10. Async Type Safety - Promise型の誤用
// ======================================
async function fetchUser(id: string): Promise<{ name: string }> {
  return { name: "test" };
}

async function incorrectUsage() {
  // エラー: awaitを忘れている
  const user = fetchUser("1");
  console.log(user.name); // エラー: Promiseにnameプロパティは存在しない
}