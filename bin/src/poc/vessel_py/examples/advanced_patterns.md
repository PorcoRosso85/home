# 高度なVesselパターン集

## 1. 自己修正器パターン

### self_modifying_vessel.py
```python
#!/usr/bin/env python3
# 実行結果に基づいて次のスクリプトを生成

import sys
import json

initial_script = sys.stdin.read()

# 初回実行
context = {'attempts': 0, 'history': []}
exec(initial_script, context)

# エラーがあれば自己修正
while context.get('error') and context['attempts'] < 3:
    context['attempts'] += 1
    
    # エラーに基づいて修正スクリプトを生成
    fix_script = f"""
# 修正試行 {context['attempts']}
try:
    {initial_script}
except {context['error'].__class__.__name__} as e:
    # 別のアプローチを試す
    print("Fallback approach")
    """
    
    exec(fix_script, context)
```

## 2. 学習器パターン

### learning_vessel.py
```python
#!/usr/bin/env python3
# 過去の実行から学習する器

import sys
import json
import os

# 履歴ファイルから学習
history_file = '/tmp/vessel_history.json'
history = []

if os.path.exists(history_file):
    with open(history_file, 'r') as f:
        history = json.load(f)

script = sys.stdin.read()

# 類似のスクリプトから最適化を提案
optimizations = []
for past in history:
    if similar(script, past['script']):
        optimizations.append(past['optimization'])

# 最適化を適用
optimized_script = apply_optimizations(script, optimizations)
exec(optimized_script)

# 実行結果を履歴に追加
history.append({
    'script': script,
    'performance': measure_performance(),
    'optimization': suggest_optimization()
})

with open(history_file, 'w') as f:
    json.dump(history[-100:], f)  # 最新100件のみ保持
```

## 3. 分岐器パターン

### branch_vessel.sh
```bash
#!/bin/bash
# 条件に応じて異なる器に振り分け

input=$(cat)

# 入力を解析
if echo "$input" | grep -q "async"; then
    # 非同期処理はBunへ
    echo "$input" | bun async_vessel.ts
elif echo "$input" | grep -q "import numpy"; then
    # 数値計算はPythonへ
    echo "$input" | python numpy_vessel.py
elif echo "$input" | grep -q "SELECT"; then
    # SQLはデータベース器へ
    echo "$input" | python sql_vessel.py
else
    # デフォルト
    echo "$input" | python vessel.py
fi
```

## 4. キャッシュ器パターン

### cache_vessel.py
```python
#!/usr/bin/env python3
# 実行結果をキャッシュする器

import sys
import hashlib
import json
import os

script = sys.stdin.read()
script_hash = hashlib.sha256(script.encode()).hexdigest()

cache_dir = '/tmp/vessel_cache'
cache_file = f'{cache_dir}/{script_hash}.json'

# キャッシュチェック
if os.path.exists(cache_file):
    with open(cache_file, 'r') as f:
        cached = json.load(f)
        if cached['ttl'] > time.time():
            print(cached['result'])
            sys.exit(0)

# 実行とキャッシュ
import io
from contextlib import redirect_stdout

output = io.StringIO()
with redirect_stdout(output):
    exec(script)

result = output.getvalue()

# キャッシュ保存
os.makedirs(cache_dir, exist_ok=True)
with open(cache_file, 'w') as f:
    json.dump({
        'result': result,
        'ttl': time.time() + 3600  # 1時間
    }, f)

print(result)
```

## 5. 検証器パターン

### validation_vessel.py
```python
#!/usr/bin/env python3
# スクリプトの安全性を検証してから実行

import sys
import ast

script = sys.stdin.read()

# 危険な操作をチェック
dangerous_patterns = [
    'eval', 'exec', '__import__',
    'open', 'file', 'input',
    'os.system', 'subprocess'
]

# ASTを解析
tree = ast.parse(script)
for node in ast.walk(tree):
    if isinstance(node, ast.Name) and node.id in dangerous_patterns:
        print(f"Error: Dangerous operation '{node.id}' detected", file=sys.stderr)
        sys.exit(1)

# 安全なら実行
exec(script, {'__builtins__': safe_builtins})
```

## 6. ストリーム器パターン

### stream_vessel.py
```python
#!/usr/bin/env python3
# ストリーミング処理用の器

import sys
import json

# ヘッダーでスクリプトを受け取る
header_line = sys.stdin.readline()
script = json.loads(header_line)['script']

# 各行に対してスクリプトを適用
line_number = 0
for line in sys.stdin:
    line_number += 1
    context = {
        'line': line.strip(),
        'line_number': line_number,
        'emit': print
    }
    exec(script, context)
```

### 使用例
```bash
# 最初の行でスクリプトを定義、以降のデータを処理
echo '{"script": "if line_number % 2 == 0: emit(line.upper())"}' | \
cat - data.txt | \
python stream_vessel.py
```

## 7. 合成器パターン

### compose_vessels.py
```python
#!/usr/bin/env python3
# 複数の器を合成する器

import sys
import json

config = json.loads(sys.stdin.read())

# 器を順次合成
composed_script = """
# 合成された器
import sys
data = sys.stdin.read()
"""

for vessel in config['vessels']:
    composed_script += f"""
# {vessel['name']}
{vessel['code']}
data = transform(data)
"""

composed_script += """
print(data)
"""

# 合成された器を出力（実行可能）
print(composed_script)
```

## まとめ

これらの高度なパターンは：

1. **自己適応** - 実行時の状況に応じて動作を変更
2. **知識の蓄積** - 過去の実行から学習
3. **安全性** - 実行前の検証とサンドボックス化
4. **効率化** - キャッシュとストリーム処理
5. **柔軟性** - 動的な器の合成と分岐