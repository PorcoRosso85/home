# 循環的複雑度（C901）ガイド

## 循環的複雑度とは

McCabe循環的複雑度は、プログラムの制御フローの複雑さを測る指標です。
簡単に言うと「コードを理解するのに必要な思考の分岐数」を表します。

## 計算方法

複雑度 = 1 + 分岐の数

### カウントされる要素
- `if` 文: +1
- `elif` 文: +1
- `for` ループ: +1
- `while` ループ: +1
- `except` 節: +1
- `and` / `or` 演算子: +1
- 三項演算子 (`x if condition else y`): +1
- リスト内包表記の `if`: +1

## 複雑度と品質の関係

| 複雑度 | 評価 | リスク |
|--------|------|---------|
| 1-10   | 良好 | 低い - 理解しやすく、テストしやすい |
| 11-20  | 要注意 | 中程度 - リファクタリングを検討 |
| 21-50  | 危険 | 高い - エラーが発生しやすい |
| 50+    | 非常に危険 | 非常に高い - 理解もテストも困難 |

## なぜ10以下が推奨されるか

### 1. 認知負荷
人間の短期記憶は一般的に7±2個の要素しか保持できません。
複雑度10を超えると、関数の全体像を頭の中で把握することが困難になります。

### 2. テストの困難さ
複雑度が高いほど、すべての実行パスをテストすることが困難になります。
- 複雑度10: 最大10個のテストケースで網羅可能
- 複雑度20: 最大20個のテストケース必要
- 複雑度44: 44個以上のテストケースが必要！

### 3. バグの温床
研究によると、複雑度とバグ発生率には強い相関があります。
複雑度が10を超えると、バグ発生率が急激に上昇します。

## リファクタリング戦略

### 1. 早期リターン（ガード節）
```python
# 悪い例 - 複雑度4
def process(data):
    if data is not None:
        if data.is_valid():
            if data.has_permission():
                return data.execute()
    return None

# 良い例 - 複雑度4（ネストが浅い）
def process(data):
    if data is None:
        return None
    if not data.is_valid():
        return None
    if not data.has_permission():
        return None
    return data.execute()
```

### 2. 関数の分割
```python
# 悪い例 - 複雑度8
def calculate_price(order):
    total = 0
    for item in order.items:
        if item.category == 'food':
            if item.is_fresh():
                total += item.price * 0.9
            else:
                total += item.price * 0.7
        elif item.category == 'electronics':
            if item.warranty:
                total += item.price * 1.1
            else:
                total += item.price
    return total

# 良い例 - 複雑度3
def calculate_price(order):
    total = 0
    for item in order.items:
        total += calculate_item_price(item)
    return total

def calculate_item_price(item):  # 複雑度5
    if item.category == 'food':
        return calculate_food_price(item)
    elif item.category == 'electronics':
        return calculate_electronics_price(item)
    return item.price

def calculate_food_price(item):  # 複雑度2
    if item.is_fresh():
        return item.price * 0.9
    return item.price * 0.7

def calculate_electronics_price(item):  # 複雑度2
    if item.warranty:
        return item.price * 1.1
    return item.price
```

### 3. 戦略パターンやディスパッチテーブル
```python
# 悪い例 - 複雑度6
def handle_command(cmd, data):
    if cmd == 'create':
        return create_item(data)
    elif cmd == 'update':
        return update_item(data)
    elif cmd == 'delete':
        return delete_item(data)
    elif cmd == 'list':
        return list_items(data)
    else:
        return error_response()

# 良い例 - 複雑度2
COMMAND_HANDLERS = {
    'create': create_item,
    'update': update_item,
    'delete': delete_item,
    'list': list_items,
}

def handle_command(cmd, data):
    handler = COMMAND_HANDLERS.get(cmd)
    if handler:
        return handler(data)
    return error_response()
```

## プロジェクトでの適用

### 現状の例: autonomous_decomposer.py
```python
def create_autonomous_decomposer(repository):  # 複雑度44！
    # 500行以上の巨大な関数
    # 多数の条件分岐とネストしたロジック
```

### リファクタリング案
1. **戦略別の関数に分割**
   - `_handle_hierarchical_strategy()`
   - `_handle_functional_strategy()`
   - `_handle_temporal_strategy()`

2. **エラーハンドリングの統一**
   - `_validate_requirement()`
   - `_handle_error_response()`

3. **ビジネスロジックの分離**
   - `_create_sub_requirements()`
   - `_save_requirements_batch()`
   - `_build_response()`

これにより、各関数の複雑度を10以下に抑えることができます。