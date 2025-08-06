#!/usr/bin/env python3
"""
Complex Python Type Patterns
TypeScriptの高度な型機能をPythonでどこまで再現できるか検証
"""

from typing import (
    TypeVar, Generic, Protocol, Union, Literal, TypeGuard, 
    overload, Callable, Any, Dict, List, Optional, 
    get_args, get_origin, cast, TYPE_CHECKING
)
from typing_extensions import TypedDict, NotRequired, Self
from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass
from functools import wraps
import json

# ======================================
# 1. Generic Constraints - ジェネリクス制約
# ======================================
class Serializable(Protocol):
    """TypeScriptのインターフェース相当"""
    def to_json(self) -> str:
        ...

T = TypeVar('T', bound=Serializable)

def serialize(obj: T) -> str:
    return obj.to_json()

# 正しい使用例
@dataclass
class User:
    name: str
    
    def to_json(self) -> str:
        return json.dumps({"name": self.name})

# serialize(User("Alice"))  # OK
# serialize(42)  # エラー: intはSerializableプロトコルを満たさない

# ======================================
# 2. Conditional Types - 条件型（Pythonでは完全な再現は困難）
# ======================================
# Pythonには条件型がないため、Union型やオーバーロードで近似

T2 = TypeVar('T2')

@overload
def unwrap_promise(value: asyncio.Future[T2]) -> T2: ...

@overload 
def unwrap_promise(value: T2) -> T2: ...

def unwrap_promise(value: Union[asyncio.Future[T2], T2]) -> T2:
    if isinstance(value, asyncio.Future):
        return value.result()
    return value

# ======================================
# 3. Type Guards & Narrowing - 型ガードとナローイング
# ======================================
def is_string(value: object) -> TypeGuard[str]:
    """TypeScriptの型ガード相当"""
    return isinstance(value, str)

def process_value(value: Union[str, int]) -> None:
    if is_string(value):
        # ここでvalueはstr型として扱われる
        print(value.upper())
    else:
        # ここでvalueはint型として扱われる
        print(f"{value:.2f}")

# ======================================
# 4. Mapped Types - マップ型（Pythonでは制限あり）
# ======================================
# Pythonには直接的なマップ型はないが、TypedDictで部分的に実現

class UserDict(TypedDict):
    name: str
    age: int

class PartialUserDict(TypedDict, total=False):
    """TypeScriptのPartial<T>相当"""
    name: str
    age: int

class ReadOnlyUserDict(TypedDict):
    """読み取り専用の近似（実行時の保証はない）"""
    name: str
    age: int

# ======================================
# 5. Recursive Types - 再帰的型定義
# ======================================
# Pythonでは前方参照を使用
JSONValue = Union[str, int, float, bool, None, 'JSONObject', 'JSONArray']
JSONObject = Dict[str, JSONValue]
JSONArray = List[JSONValue]

# 型チェッカーが再帰を解決
valid_json: JSONValue = {
    "name": "test",
    "values": [1, 2, {"nested": True}],
    "metadata": None
}

# ======================================
# 6. Higher-Order Function Types - 高階関数の型
# ======================================
F = TypeVar('F', bound=Callable[..., Any])

def memoize(fn: F) -> F:
    """デコレータの型保持"""
    cache: Dict[str, Any] = {}
    
    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = fn(*args, **kwargs)
        return cache[key]
    
    return cast(F, wrapper)

@memoize
def add(a: int, b: int) -> int:
    return a + b

# memoize("not a function")  # エラー: strはCallableではない

# ======================================
# 7. Exhaustive Check - Union型の網羅性チェック
# ======================================
Status = Literal['pending', 'success', 'error', 'cancelled']

def handle_status(status: Status) -> str:
    if status == 'pending':
        return 'Processing...'
    elif status == 'success':
        return 'Completed!'
    elif status == 'error':
        return 'Failed!'
    elif status == 'cancelled':
        return 'Cancelled!'
    else:
        # 型チェッカーはここに到達しないことを認識
        assert_never(status)

def assert_never(value: Any) -> None:
    """TypeScriptのnever型チェック相当"""
    raise AssertionError(f"Unhandled value: {value}")

# ======================================
# 8. Template Literal Types - テンプレートリテラル型
# ======================================
# Pythonには直接的なテンプレートリテラル型はない
# Literal型の組み合わせで近似
EventName = Literal['click', 'focus', 'blur']
EventHandler = Literal['onClick', 'onFocus', 'onBlur']

# 手動でのマッピングが必要
def get_handler_name(event: EventName) -> EventHandler:
    mapping: Dict[EventName, EventHandler] = {
        'click': 'onClick',
        'focus': 'onFocus', 
        'blur': 'onBlur'
    }
    return mapping[event]

# ======================================
# 9. Intersection Types - 交差型（Pythonでは多重継承やProtocolで実現）
# ======================================
class Timestamped(Protocol):
    created_at: str
    updated_at: str

class Identifiable(Protocol):
    id: str

class UserProtocol(Protocol):
    name: str
    email: str

# 複数のProtocolを満たす型
class CompleteUser:
    def __init__(self, id: str, name: str, email: str):
        self.id = id
        self.name = name
        self.email = email
        self.created_at = "2024-01-01"
        self.updated_at = "2024-01-01"

def process_complete_user(user: UserProtocol) -> None:
    # ProtocolベースでチェックはTypeScriptより弱い
    print(user.name)

# ======================================
# 10. Async Type Safety - 非同期処理の型安全性
# ======================================
async def fetch_user(user_id: str) -> Dict[str, str]:
    # 実際のAPIコールの代わりにダミーデータ
    await asyncio.sleep(0.1)
    return {"name": f"User {user_id}"}

async def process_users(ids: List[str]) -> List[Dict[str, str]]:
    # asyncio.gatherの型推論
    users = await asyncio.gather(*[fetch_user(id) for id in ids])
    return list(users)  # 型は正しく推論される

# エラー例
async def incorrect_usage() -> None:
    # awaitを忘れた場合
    user = fetch_user("1")  # 型: Coroutine[Any, Any, Dict[str, str]]
    # print(user["name"])  # エラー: Coroutineに[]演算子は使えない

# ======================================
# 追加設定や特別な対応が必要な部分
# ======================================
"""
Pythonで TypeScript相当の型安全性を実現するための追加要件：

1. **型チェッカーの設定**
   - pyrightconfig.json で "strict" モード必須
   - "reportUnknownMemberType": "error" など細かい設定が必要

2. **追加ライブラリ**
   - typing_extensions: 最新の型機能
   - mypy_extensions: mypyを使う場合

3. **Pythonでは実現困難な機能**
   - 真の条件型（Conditional Types）
   - テンプレートリテラル型の自動生成
   - Mapped Typesの完全な再現
   - 構造的部分型の厳密なチェック

4. **運用上の注意点**
   - 型アノテーションが冗長になりがち
   - Protocol使用時のパフォーマンスへの影響
   - 実行時の型チェックは別途実装が必要
   - IDEサポートがTypeScriptより劣る場合がある
"""