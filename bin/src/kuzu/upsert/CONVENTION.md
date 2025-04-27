# コーディング規約 (CONVENTION)

## 基本原則

このプロジェクトでは、関数型プログラミングの原則に可能な限り従います。これにより、コードの予測可能性、テスト容易性、保守性が向上します。

## 型定義とエラー処理

### 型定義

- すべての型定義は `TypedClass` を使用してください
- 各層の `types.py` ファイルに型定義を集約します
- 可能な限り型アノテーションを使用してください

```python
# 良い例
from typing import TypedDict, List, Optional

class FunctionData(TypedDict):
    title: str
    description: Optional[str]
    type: str
    pure: bool
    parameters: List["ParameterData"]
```

### エラー処理

- 例外を投げる代わりに、定義したエラー型を返却してください
- 関数の戻り値として成功/失敗を表現してください
- Result型は使用せず、以下の2+1種類の列挙型/共用体型を使用してください：
  * 成功時の戻り値型
  * 例外時の戻り値型
  * （オプション）副作用型

```python
# 良い例
from typing import TypedDict, Union, Literal

class FunctionData(TypedDict):
    title: str
    description: str
    parameters: List[str]

class FunctionError(TypedDict):
    code: str
    message: str

# 成功型とエラー型の共用体型として定義
FunctionResult = Union[FunctionData, FunctionError]

def add_function(data: dict) -> FunctionResult:
    if not validate_data(data):
        return {"code": "INVALID_DATA", "message": "Invalid data"}
    
    # 処理...
    
    return {
        "title": result_title,
        "description": result_description,
        "parameters": result_parameters
    }

# エラーかどうかの判別関数
def is_error(result: FunctionResult) -> bool:
    return "code" in result and "message" in result
```

## 禁止事項

以下の構文や機能は使用しないでください：

### クラス

- `class` キーワードを使用したクラス定義は避けてください
- オブジェクト指向設計の代わりに、関数とデータの明確な分離を行ってください

```python
# 避けるべき例
class FunctionRepository:
    def __init__(self, connection):
        self.connection = connection
    
    def save(self, function):
        # ...

# 良い例
def create_function_repository(connection):
    def save(function):
        # ...
    
    def find_by_id(function_id):
        # ...
    
    return {
        "save": save,
        "find_by_id": find_by_id
    }
```

### 例外

- `try`/`except` ブロックや例外の使用は避けてください
- `raise` や `Exception` の派生クラスは使用しないでください
- 代わりに、明示的なエラー型とエラーハンドリング関数を使用してください

```python
# 避けるべき例
def divide(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        raise ValueError("Cannot divide by zero")

# 良い例
def divide(a, b):
    if b == 0:
        return {"status": "error", "message": "Cannot divide by zero", "code": "ZERO_DIVISION"}
    return {"status": "success", "data": a / b}
```

## 推奨される実装スタイル

### 関数のみで実装

- 可能な限り純粋関数（同じ入力に対して常に同じ出力を返し、副作用のない関数）を使用してください
- 状態を持つオブジェクトの代わりに、関数のクロージャを活用してください
- 高階関数（関数を引数として受け取るか、関数を返す関数）を活用してください

```python
# 良い例
def create_validator(schema):
    def validate(data):
        # schemaを使ってdataを検証
        # ...
        return is_valid, error_message
    
    return validate

# 使用例
validate_function = create_validator(function_schema)
is_valid, error = validate_function(data)
```

### 不変性の確保

- データの変更は避け、新しいデータ構造を返してください
- リスト操作には `map`、`filter`、`reduce` などの高階関数を使用してください

```python
# 避けるべき例
def add_parameter(function, parameter):
    function["parameters"].append(parameter)
    return function

# 良い例
def add_parameter(function, parameter):
    return {
        **function,
        "parameters": [*function["parameters"], parameter]
    }
```

## ファイル構造とモジュール設計

- 各モジュールは明確に定義された単一の責任を持つべきです
- 関連する関数をモジュールにグループ化してください
- 循環依存を避けるために、依存関係グラフを意識してください

## テスト

- すべての関数にユニットテストを書いてください
- テストは関数の入出力のみに焦点を当ててください
- モックやスタブを活用して依存関係を分離してください
- 別途テストファイルは作成せず、実装ファイル内に単体テストを記述してください
- テストは目的を明確に示す命名を使用してください
- テストはpytestの規約に従って記述してください（assert文を使用）
- `if __name__ == "__main__":` ブロック内にテストケースを記述し、ファイル単体実行時にテストが実行されるようにしてください

```python
# 実装例
def add(a: int, b: int) -> int:
    return a + b

# テスト関数
def verify_addition():
    assert add(1, 2) == 3
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

# テスト実行
if __name__ == "__main__":
    import sys
    import pytest
    
    # このモジュールのテストを実行
    pytest.main([__file__])
    
    # または以下のように独自のテスト実行ロジックを実装することも可能
    # verify_addition()
    # print("All tests passed!")
```

## ドキュメント

- すべての関数に適切なドキュメント文字列を書いてください
- パラメータの型と戻り値の型を文書化してください
- 複雑なロジックには説明コメントを追加してください

## 設定管理

- デフォルト設定は一切禁止
- デフォルト引数も同様にデフォルト設定なので禁止
- 設定箇所は以下のみを許可する
  * infrastructure/variables.py
