#!/usr/bin/env python3
"""
Complex Python Type Patterns - Error Examples
コメントを外してエラー検出を確認
"""

from typing import (
    TypeVar, Protocol, Union, Literal, TypeGuard, 
    overload, Callable, Any, Dict, List,
    get_args, get_origin, cast
)
from typing_extensions import TypedDict, assert_never
import asyncio
from dataclasses import dataclass
import json

# ======================================
# 1. Generic Constraints - ジェネリクス制約違反
# ======================================
class Serializable(Protocol):
    def to_json(self) -> str:
        ...

T = TypeVar('T', bound=Serializable)

def serialize(obj: T) -> str:
    return obj.to_json()

# エラー: intはSerializableプロトコルを満たさない
serialize(42)

# ======================================
# 2. Conditional Types - 条件型のエラー（オーバーロードで近似）
# ======================================
# Pythonでは条件型の完全な再現は困難
# Union型の誤用で代替
ErrorCheck: Literal[True] = False  # エラー: FalseをLiteral[True]に代入

# ======================================
# 3. Type Guards - 誤った型アサーション
# ======================================
def process_value(value: Union[str, int]) -> None:
    # エラー: intの可能性があるのにstring専用メソッドを使用
    print(value.upper())

# ======================================
# 4. Mapped Types - readonly違反（Pythonでは限定的）
# ======================================
class ReadOnlyUserDict(TypedDict):
    name: str
    age: int

user: ReadOnlyUserDict = {"name": "Alice", "age": 30}
# Python の TypedDict は実行時の readonly を強制しないが、
# 型チェッカーは警告を出すべき（設定次第）
user["name"] = "Bob"  # 実行時エラーにはならないが、意図的には readonly

# ======================================
# 5. Recursive Types - 型の不一致
# ======================================
JSONValue = Union[str, int, float, bool, None, 'JSONObject', 'JSONArray']
JSONObject = Dict[str, JSONValue]
JSONArray = List[JSONValue]

# エラー: undefined は JSONValue に含まれない（Pythonにはundefinedがない）
# 代わりに無効な型を使用
invalid_json: JSONValue = {"value": object()}  # object型は許可されていない

# ======================================
# 6. Higher-Order Functions - 引数の型不一致
# ======================================
F = TypeVar('F', bound=Callable[..., Any])

def memoize(fn: F) -> F:
    return fn  # 簡略化

# エラー: 文字列は関数ではない
memoize("not a function")

# ======================================
# 7. Exhaustive Check - 処理漏れ
# ======================================
Status = Literal['pending', 'success', 'error', 'cancelled']

def incomplete_handler(status: Status) -> str:
    if status == 'pending':
        return 'Processing...'
    elif status == 'success':
        return 'Completed!'
    # errorとcancelledの処理が漏れている
    else:
        # エラー: 'error' | 'cancelled' がnever相当に到達
        assert_never(status)

# ======================================
# 8. Template Literal Types - 無効なパターン
# ======================================
# Pythonには直接的なテンプレートリテラル型はない
EventHandler = Literal['onClick', 'onFocus', 'onBlur']
handler: EventHandler = "onHover"  # エラー: "onHover"は有効なEventHandlerではない

# ======================================
# 9. Intersection Types - プロパティ不足
# ======================================
@dataclass
class CompleteUser:
    id: str
    name: str
    email: str
    created_at: str
    updated_at: str

# エラー: idプロパティが不足
invalid_user = CompleteUser(
    name="Bob",
    email="bob@example.com",
    created_at="2024-01-01",
    updated_at="2024-01-01"
    # id が不足
)

# ======================================
# 10. Async Type Safety - Promise型の誤用
# ======================================
async def fetch_user(user_id: str) -> Dict[str, str]:
    await asyncio.sleep(0.1)
    return {"name": f"User {user_id}"}

async def incorrect_usage() -> None:
    # エラー: awaitを忘れている
    user = fetch_user("1")  # Coroutine型
    print(user["name"])  # エラー: Coroutineに[]演算子は使えない