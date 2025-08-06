# Python typing module + pyrightの限界

## 前提条件
- Python 3.12 + 最新のtyping機能をすべて使用
- pyright strictモード
- typing_extensionsも含む

## TypeScriptにあってPythonに存在しない機能

### 1. 条件型（Conditional Types）
```typescript
// TypeScript: 型レベルでの条件分岐
type IsArray<T> = T extends any[] ? true : false;
type Test1 = IsArray<string[]>;  // true
type Test2 = IsArray<string>;    // false

// 実用例: Promiseを自動でアンラップ
type Awaited<T> = T extends Promise<infer U> ? U : T;
```

```python
# Python: 不可能
# overloadは値レベルの分岐であり、型レベルの条件分岐ではない
@overload
def process(x: list[Any]) -> Literal[True]: ...
@overload  
def process(x: Any) -> Literal[False]: ...
# これは関数の実装であり、型定義ではない
```

### 2. テンプレートリテラル型（Template Literal Types）
```typescript
// TypeScript: 文字列パターンの型レベル生成
type EventName = 'click' | 'focus' | 'blur';
type EventHandler = `on${Capitalize<EventName>}`;
// 自動的に 'onClick' | 'onFocus' | 'onBlur' が生成される

// 実用例: APIエンドポイントの型安全な生成
type API<T extends string> = `/api/${T}` | `/api/${T}/:id`;
type UserAPI = API<'users'>;  // '/api/users' | '/api/users/:id'
```

```python
# Python: 手動列挙しかできない
EventHandler = Literal['onClick', 'onFocus', 'onBlur']
# 新しいイベントを追加するたびに手動で更新が必要
```

### 3. Mapped Types（マップ型）
```typescript
// TypeScript: 既存の型から新しい型を自動生成
type Readonly<T> = {
  readonly [P in keyof T]: T[P];
};

type Partial<T> = {
  [P in keyof T]?: T[P];
};

type Getters<T> = {
  [P in keyof T as `get${Capitalize<P>}`]: () => T[P];
};
```

```python
# Python: 各型を個別に定義する必要がある
# TypedDictでは動的なキー生成は不可能
class User(TypedDict):
    name: str
    age: int

class PartialUser(TypedDict, total=False):
    name: str  # 手動で再定義
    age: int   # 手動で再定義

# Getters相当は作成不可能
```

### 4. keyof演算子
```typescript
// TypeScript: オブジェクトのキーを型として取得
type User = { name: string; age: number; email: string };
type UserKeys = keyof User;  // 'name' | 'age' | 'email'

function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
    return obj[key];
}
```

```python
# Python: 実現不可能
# Literal['name', 'age', 'email'] を手動で定義するしかない
UserKeys = Literal['name', 'age', 'email']
# 元の型定義が変更されても自動更新されない
```

### 5. typeof演算子（型の抽出）
```typescript
// TypeScript: 値から型を抽出
const config = {
    apiUrl: 'https://api.example.com',
    timeout: 5000,
    retries: 3
} as const;

type Config = typeof config;
// 自動的に { apiUrl: string; timeout: number; retries: number } 型
```

```python
# Python: 値から型を自動抽出する機能なし
# 型を別途定義する必要がある
class Config(TypedDict):
    apiUrl: str
    timeout: int
    retries: int

config: Config = {
    "apiUrl": "https://api.example.com",
    "timeout": 5000,
    "retries": 3
}
```

### 6. infer（型の推論）
```typescript
// TypeScript: 型から部分的な型を抽出
type ReturnType<T> = T extends (...args: any[]) => infer R ? R : never;
type UnpackArray<T> = T extends (infer U)[] ? U : T;
```

```python
# Python: inferに相当する機能なし
# 型パラメータの部分的な抽出は不可能
```

### 7. 再帰的条件型
```typescript
// TypeScript: 深いネストの型変換
type DeepReadonly<T> = {
  readonly [P in keyof T]: T[P] extends object ? DeepReadonly<T[P]> : T[P];
};
```

```python
# Python: 再帰的な型変換は手動実装のみ
# 自動的な深い変換は不可能
```

## 実務での影響

### TypeScriptで可能な型安全なAPIクライアント
```typescript
type APIEndpoints = {
  '/users': { method: 'GET'; response: User[] };
  '/users/:id': { method: 'GET'; response: User };
  '/users': { method: 'POST'; body: CreateUser; response: User };
};

// 型安全なfetch関数（エンドポイントとメソッドの組み合わせを検証）
function api<T extends keyof APIEndpoints>(
  endpoint: T,
  config: APIEndpoints[T]
): Promise<APIEndpoints[T]['response']> {
  // 実装
}
```

### Pythonでの限界
```python
# エンドポイントごとに個別の関数を定義するしかない
async def get_users() -> list[User]: ...
async def get_user(id: str) -> User: ...
async def create_user(data: CreateUser) -> User: ...
# 型レベルでの統一的な管理は不可能
```

## 結論

typing moduleをフル活用しても、以下は**絶対に実現不可能**：

1. **型レベルの計算・変換**
   - 条件型
   - テンプレートリテラル型
   - Mapped Types

2. **型の自動抽出・生成**
   - keyof
   - typeof
   - infer

3. **高度な型の組み合わせ**
   - 再帰的条件型
   - 型レベルのパターンマッチング

これらの機能がないため、Pythonでは：
- より多くのボイラープレートコードが必要
- 型定義の重複が避けられない
- 型の一貫性を手動で維持する必要がある

**TypeScriptの型システムの表現力を100%とすると、Pythonは60-70%程度**が現実的な評価です。