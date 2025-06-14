# 規則

返却型の例, 成功と例外をユニオン使用して記載すること
```python
from src.domain.result import ValidationError

def func() -> str:
  try:
    return str(...)
  except:
    raise ValidationError(...)
```
可能ならクラスは使わない
ファイルをモジュール・一つのクラスとみなせる場合はそうすること
仮に状態変化を保持したい場合、クラスの使用を検討してよいが、劣後とすること
絶対インポートではなく相対インポートとすること、理由は各ファイルの依存関係を明確にするためである
型アノテーションはすべての個所に使用する、変数についても
各ファイルに各関数一つを基本としている、その関数の動作を確認するテストは必ず記述する。
例:
```python
def func():
  return

from src import dbg
if dbg.is_pytest():
  import pytest
  def test_func():
    assert ...
```
