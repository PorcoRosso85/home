"""
型安全性検証用Pythonサンプル
統一規約に基づく実装での型チェック動作確認
"""
from typing import Optional, List, Dict, Union
from dataclasses import dataclass
from pydantic import BaseModel, validator


# 1. 基本的な型ヒント
def add_numbers(a: int, b: int) -> int:
    """型ヒント付き関数"""
    return a + b


# 2. Dataclassによる型定義
@dataclass
class Person:
    name: str
    age: int
    email: Optional[str] = None


# 3. Pydanticによる実行時型検証
class ValidatedPerson(BaseModel):
    name: str
    age: int
    email: Optional[str] = None
    
    @validator('age')
    def age_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Age must be positive')
        return v


# 4. 複雑な型定義
Repository = Dict[str, Union[str, List[Dict[str, str]]]]


def process_repository(repo: Repository) -> Optional[str]:
    """複雑な型を扱う関数"""
    if "name" in repo and isinstance(repo["name"], str):
        return repo["name"]
    return None


# 5. 型エラーを含むコード（型チェッカーが検出すべき）
def problematic_function():
    # これらは型チェッカーが警告を出すべき
    result = add_numbers("1", "2")  # 型エラー: str vs int
    person = Person(name=123, age="twenty")  # 型エラー
    return result


if __name__ == "__main__":
    # 正しい使用例
    print(add_numbers(1, 2))
    person = Person(name="Alice", age=30)
    print(person)
    
    # Pydanticによる実行時検証
    try:
        validated = ValidatedPerson(name="Bob", age=-5)  # 実行時エラー
    except ValueError as e:
        print(f"Validation error: {e}")