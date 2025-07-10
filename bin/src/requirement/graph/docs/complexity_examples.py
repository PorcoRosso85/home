"""循環的複雑度（C901）の例"""

# 複雑度1 - 分岐なし
def simple_function():
    return 42


# 複雑度2 - if文1つ
def check_positive(n):
    if n > 0:  # +1
        return True
    return False


# 複雑度3 - if-elif
def get_grade(score):
    if score >= 90:  # +1
        return 'A'
    elif score >= 80:  # +1
        return 'B'
    return 'C'


# 複雑度4 - 複数の条件
def validate_input(value, min_val, max_val):
    if value is None:  # +1
        return False
    if value < min_val:  # +1
        return False
    if value > max_val:  # +1
        return False
    return True


# 複雑度6 - ループと条件
def count_valid_items(items):
    count = 0
    for item in items:  # +1
        if item is None:  # +1
            continue
        if item.is_valid():  # +1
            count += 1
        elif item.can_repair():  # +1
            if repair(item):  # +1
                count += 1
    return count


# 複雑度11 - 複雑すぎる例（規約違反！）
def process_order(order):
    if order is None:  # +1
        return None

    if order.status == 'pending':  # +1
        if order.payment_method == 'credit':  # +1
            if validate_credit_card(order):  # +1
                process_payment(order)
            else:
                return 'invalid_card'
        elif order.payment_method == 'debit':  # +1
            if check_balance(order):  # +1
                process_payment(order)
            else:
                return 'insufficient_funds'
    elif order.status == 'processing':  # +1
        if order.items:  # +1
            for item in order.items:  # +1
                if item.in_stock():  # +1
                    reserve_item(item)

    return order


# リファクタリング例 - 複雑度を下げる
def process_order_refactored(order):
    """複雑度3に削減"""
    if order is None:  # +1
        return None

    if order.status == 'pending':  # +1
        return process_pending_order(order)
    elif order.status == 'processing':  # +1
        return process_active_order(order)

    return order


def process_pending_order(order):
    """支払い処理を分離 - 複雑度4"""
    if order.payment_method == 'credit':  # +1
        return process_credit_payment(order)
    elif order.payment_method == 'debit':  # +1
        return process_debit_payment(order)
    return order


def process_credit_payment(order):
    """クレジット処理 - 複雑度2"""
    if validate_credit_card(order):  # +1
        process_payment(order)
        return order
    return 'invalid_card'


def process_debit_payment(order):
    """デビット処理 - 複雑度2"""
    if check_balance(order):  # +1
        process_payment(order)
        return order
    return 'insufficient_funds'


def process_active_order(order):
    """在庫処理 - 複雑度3"""
    if not order.items:  # +1
        return order

    for item in order.items:  # +1
        process_item_stock(item)

    return order


def process_item_stock(item):
    """個別アイテム処理 - 複雑度2"""
    if item.in_stock():  # +1
        reserve_item(item)
