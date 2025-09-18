# TypeScript同等の型安全性に必要な最小要件

## 必須ライブラリ・ツール

### 1. 基本セット（これだけでは不十分）
- ✅ pyright
- ✅ TypedDict（Python 3.8+標準）

### 2. 追加で必要な型機能

#### typing標準ライブラリから
```python
from typing import (
    Protocol,      # インターフェース相当
    TypeVar,       # ジェネリクス
    Union,         # ユニオン型
    Literal,       # リテラル型
    TypeGuard,     # 型ガード（3.10+）
    overload,      # オーバーロード
    cast,          # 型キャスト
    Final,         # readonly相当
    TypeAlias,     # 型エイリアス（3.10+）
)
```

#### typing_extensions（後方互換性）
```python
from typing_extensions import (
    TypedDict,     # Python < 3.8
    Protocol,      # Python < 3.8
    Literal,       # Python < 3.8
    TypeGuard,     # Python < 3.10
    NotRequired,   # オプショナルキー（3.11+）
    Self,          # 自己参照型（3.11+）
    assert_never,  # exhaustive check（3.11+）
)
```

## TypeScriptとの機能対応表

| TypeScript機能 | Python対応 | 追加要件 |
|---------------|-----------|----------|
| interface | Protocol | typing.Protocol |
| type alias | TypeAlias | typing.TypeAlias |
| generics <T> | TypeVar | typing.TypeVar |
| union \| | Union/\| | typing.Union |
| literal types | Literal | typing.Literal |
| type guards | TypeGuard | typing.TypeGuard |
| readonly | Final | typing.Final（完全ではない） |
| as const | Literal | 手動で指定 |
| keyof | ❌ | 対応なし |
| typeof | ❌ | 対応なし |
| conditional types | ❌ | overloadで部分対応 |
| template literals | ❌ | 対応なし |
| mapped types | ❌ | TypedDictで部分対応 |

## 最小構成での実装例

### TypeScript
```typescript
// 1行で条件型を定義
type Result<T> = T extends string ? number : boolean;

// テンプレートリテラル型
type Handler = `on${Capitalize<'click' | 'focus'>}`;

// Mapped Type
type Readonly<T> = { readonly [K in keyof T]: T[K] };
```

### Python（最大限の努力をしても）
```python
# 条件型は不可能、overloadで近似
@overload
def process(value: str) -> int: ...
@overload
def process(value: int) -> bool: ...

# テンプレートリテラル型は不可能、手動定義
Handler = Literal['onClick', 'onFocus']

# Mapped Typeは不可能、個別定義
class ReadonlyUser(TypedDict):
    name: str  # readonlyは実行時に強制されない
```

## 結論

**TypedDict + pyrightだけでは不十分**な理由：

1. **Protocol** - インターフェース定義に必須
2. **TypeVar** - ジェネリクスに必須
3. **Literal** - 厳密な型制約に必須
4. **TypeGuard** - 型ナローイングに必須
5. **Union** - 複数型の表現に必須

さらに、以下はPythonでは**実現不可能**：
- 条件型（Conditional Types）
- テンプレートリテラル型
- 完全なMapped Types
- keyof/typeof演算子

つまり、TypeScriptの**60-70%程度**までしか到達できません。