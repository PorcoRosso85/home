# コード複雑度規約

## 目的
コードの可読性と保守性を高めるため、複雑度に関する制限を設ける。

## ネスト深さ制限

### 最大ネスト深さ: 4
- if文、for文、while文、with文などのブロックのネスト深さは最大4レベルまで
- それ以上深いネストが必要な場合は、関数に分割する

### 悪い例
```python
def process_data(data):
    if data:
        for item in data:
            if item.is_valid():
                with open(item.path) as f:
                    for line in f:
                        if line.strip():  # ネスト深さ5 - 規約違反！
                            process_line(line)
```

### 良い例
```python
def process_data(data):
    if not data:
        return
    
    for item in data:
        process_item(item)

def process_item(item):
    if not item.is_valid():
        return
        
    with open(item.path) as f:
        process_file(f)

def process_file(file):
    for line in file:
        if line.strip():
            process_line(line)
```

## 循環的複雑度制限

### 最大複雑度: 10
- McCabe循環的複雑度は10以下に保つ
- 一つの関数内の分岐（if、elif、for、while、except等）が多すぎる場合は分割

### 測定方法
```bash
# lintで複雑度をチェック
nix run .#lint

# 特定ファイルのみチェック
nix run .#lint -- path/to/file.py
```

## Early Return パターンの推奨

### ネストを減らすテクニック
1. **ガード節の使用**
   ```python
   # 悪い例
   def calculate(value):
       if value > 0:
           result = value * 2
           return result
       else:
           return None
   
   # 良い例
   def calculate(value):
       if value <= 0:
           return None
       return value * 2
   ```

2. **continue/breakの活用**
   ```python
   # 悪い例
   for item in items:
       if item.is_valid():
           if item.needs_processing():
               process(item)
   
   # 良い例
   for item in items:
       if not item.is_valid():
           continue
       if not item.needs_processing():
           continue
       process(item)
   ```

## ツールによる自動チェック

### Ruffの設定（pyproject.toml）
```toml
[tool.ruff.mccabe]
max-complexity = 10

[tool.ruff.pylint]
max-nested-blocks = 4
```

### 使用方法
```bash
# チェックのみ
nix run .#lint

# 自動修正可能な問題を修正
nix run .#lint.fix

# コードフォーマット
nix run .#format
```

## 例外
以下の場合は、複雑度制限を超えることを許可する：
1. テストコード（ただし、可能な限り守ることを推奨）
2. 外部ライブラリとの互換性のため避けられない場合
3. パフォーマンス上の理由で分割が望ましくない場合（要コメント）

例外を適用する場合は、コメントで理由を明記すること：
```python
# ruff: noqa: C901  # 外部APIの仕様により複雑な分岐が必要
def complex_api_handler():
    ...
```