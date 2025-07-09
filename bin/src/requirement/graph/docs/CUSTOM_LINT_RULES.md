# カスタムLintルールの実装方法

## 1ファイル1公開関数ルールについて

Ruffには直接このようなルールはありませんが、いくつかの方法で実現できます。

## 方法1: Ruff Plugin（推奨）

```python
# custom_rules.py
from typing import Type
from ruff.violation import Violation
from ruff.checker import Checker

class OnePublicFunctionPerFile(Violation):
    """各ファイルは1つの公開関数のみをエクスポートすべき"""
    code = "PLR9001"
    message = "ファイルに複数の公開関数があります: {names}"

def check_one_public_function(checker: Checker) -> None:
    """公開関数の数をチェック"""
    public_functions = []
    
    for node in checker.tree.body:
        if isinstance(node, ast.FunctionDef):
            if not node.name.startswith('_'):
                public_functions.append(node.name)
    
    if len(public_functions) > 1:
        checker.add_violation(
            OnePublicFunctionPerFile(
                names=", ".join(public_functions)
            )
        )
```

## 方法2: 命名規約での実装（現実的）

```python
# ファイル名: create_user_service.py

# ✅ 良い例: 1つの公開関数
def create_user_service(repository):
    """メインの公開関数"""
    
    def _validate_user(data):
        """内部関数（アンダースコア始まり）"""
        pass
    
    def _save_user(user):
        """内部関数"""
        pass
    
    return {
        "create": lambda data: _save_user(_validate_user(data))
    }

# ❌ 悪い例: 複数の公開関数
def create_user(data):
    pass

def update_user(data):  # 2つ目の公開関数！
    pass
```

## 方法3: Pre-commitフックでチェック

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: check-single-export
        name: Check single public function per file
        entry: python scripts/check_single_export.py
        language: python
        files: \.py$
```

```python
# scripts/check_single_export.py
import ast
import sys
from pathlib import Path

def check_file(filepath):
    with open(filepath) as f:
        tree = ast.parse(f.read())
    
    public_functions = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            if not node.name.startswith('_'):
                public_functions.append(node.name)
    
    if len(public_functions) > 1:
        print(f"{filepath}: 複数の公開関数: {public_functions}")
        return False
    return True

def main():
    errors = False
    for filepath in sys.argv[1:]:
        if not check_file(filepath):
            errors = True
    
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()
```

## 方法4: プロジェクトの規約として

### ディレクトリ構造で強制
```
application/
├── user_service.py      # create_user_service()のみ公開
├── order_service.py     # create_order_service()のみ公開
└── payment_service.py   # create_payment_service()のみ公開
```

### __all__での制限
```python
# user_service.py
__all__ = ['create_user_service']  # 1つだけエクスポート

def create_user_service():
    pass

def helper_function():  # エクスポートされない
    pass
```

## 推奨アプローチ

1. **短期的**: 命名規約（`_`プレフィックス）で内部関数を明示
2. **中期的**: `__all__`でエクスポートを制限
3. **長期的**: カスタムlintルールまたはpre-commitフック

## 既存のRuffルールで近いもの

- **PLR0913**: 引数が多すぎる関数
- **PLR0915**: ステートメントが多すぎる関数
- **PLR0912**: 分岐が多すぎる関数

これらを組み合わせることで、関数の責務を小さく保つことは可能です。