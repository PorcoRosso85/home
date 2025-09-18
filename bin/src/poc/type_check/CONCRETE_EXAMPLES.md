# 具体例: TypedDict + pyrightだけでは解決できないケース

## 1. インターフェース/プロトコル

### 問題: メソッドを持つ型の定義
```python
# TypedDictではメソッドを定義できない
class Serializable(TypedDict):  # ❌ エラー
    to_json: Callable[[], str]  # TypedDictはメソッドを持てない

# Protocolが必要
from typing import Protocol
class Serializable(Protocol):  # ✅ 
    def to_json(self) -> str: ...
```

## 2. ジェネリクス

### 問題: 型パラメータ付き関数
```python
# TypedDictだけでは型パラメータを使えない
def identity(value):  # 型情報が失われる
    return value

# TypeVarが必要
from typing import TypeVar
T = TypeVar('T')
def identity(value: T) -> T:  # ✅ 型が保持される
    return value
```

## 3. ユニオン型

### 問題: 複数の型を受け入れる
```python
# TypedDictだけでは表現できない
def process(value):  # str | int を表現できない
    if isinstance(value, str):
        return value.upper()
    return value * 2

# Unionが必要
from typing import Union
def process(value: Union[str, int]) -> Union[str, int]:  # ✅
    if isinstance(value, str):
        return value.upper()
    return value * 2
```

## 4. リテラル型

### 問題: 特定の値のみを許可
```python
# TypedDictだけでは特定の文字列値を制限できない
class Status(TypedDict):
    state: str  # "pending", "success", "error" のみを許可したい

# Literalが必要
from typing import Literal
class Status(TypedDict):
    state: Literal['pending', 'success', 'error']  # ✅
```

## 5. 型ガード

### 問題: 型の絞り込み
```python
# pyrightは自動的に型を絞り込めない場合がある
def process(value: object) -> None:
    if hasattr(value, 'name'):  # valueの型は絞り込まれない
        print(value.name)  # エラー: objectにnameがない

# TypeGuardが必要
from typing import TypeGuard
def has_name(value: object) -> TypeGuard[HasName]:
    return hasattr(value, 'name')

def process(value: object) -> None:
    if has_name(value):  # ✅ valueはHasName型として扱われる
        print(value.name)
```

## 実際のプロジェクトでの影響

### APIレスポンスの型定義（TypedDictのみ）
```python
# 限定的な表現力
class UserResponse(TypedDict):
    id: int
    name: str
    status: str  # "active" | "inactive" を強制できない
    data: dict  # 具体的な型を指定できない
```

### 完全な型定義（追加ライブラリ使用）
```python
from typing import Union, Literal, TypeVar, Generic

T = TypeVar('T')

class Response(TypedDict, Generic[T]):
    id: int
    name: str
    status: Literal['active', 'inactive']
    data: T

# 使用例
user_response: Response[UserData] = {
    "id": 1,
    "name": "Alice",
    "status": "active",  # "pending"だとエラー
    "data": user_data
}
```

## まとめ

TypedDict + pyrightだけでは：
- ❌ メソッドを持つ型を定義できない
- ❌ ジェネリクスを使えない
- ❌ ユニオン型を表現できない
- ❌ 値を制限できない（リテラル型）
- ❌ 型ガードを書けない

**最低限**必要なのは：
```python
from typing import (
    Protocol,   # インターフェース
    TypeVar,    # ジェネリクス
    Union,      # ユニオン型
    Literal,    # リテラル型
    TypeGuard,  # 型ガード
)
```

これらを使っても、TypeScriptの以下の機能は再現不可：
- 条件型
- テンプレートリテラル型
- 完全なMapped Types
- keyof/typeof