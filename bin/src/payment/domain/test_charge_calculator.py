import pytest
from . import charge_calculator

# -----------------------------------------------------------------------------
# 仕様テンプレート：以下のテストを参考に、決済の仕様を決定してください。
# これらのテストは、charge_calculator.py が実装されるまで「失敗」し続けます。
# -----------------------------------------------------------------------------

def test_specification_for_single_usage():
    """
    仕様検討ポイント①：単一の利用記録から請求額をどう計算するか？
    - 例：単価 10円, 利用量 5単位 => 50円
    """
    usage_records = [{"user_id": "user1", "quantity": 5}]
    unit_price = 10
    
    # TODO: 期待される結果を仕様として定義する
    expected = 50  # 仮の期待値
    
    actual = charge_calculator.calculate(usage_records, unit_price)
    
    assert actual == expected, "単一利用記録の計算仕様を定義してください"

def test_specification_for_multiple_usages():
    """
    仕様検討ポイント②：複数の利用記録をどう扱うか？
    - 例：利用量を合算してから単価をかけるのか？
    """
    usage_records = [
        {"user_id": "user1", "quantity": 5},
        {"user_id": "user1", "quantity": 3},
    ]
    unit_price = 10

    # TODO: 期待される結果を仕様として定義する
    expected = 80  # 仮の期待値
    
    actual = charge_calculator.calculate(usage_records, unit_price)
    
    assert actual == expected, "複数利用記録の計算仕様を定義してください"

def test_specification_for_no_usage():
    """
    仕様検討ポイント③：利用記録がない場合の請求額はどうなるか？
    - 例：0円になるべき
    """
    usage_records = []
    unit_price = 10
    
    expected = 0
    
    actual = charge_calculator.calculate(usage_records, unit_price)
    
    assert actual == expected, "利用がない場合の仕様を定義してください"

@pytest.mark.skip(reason="段階料金など、より複雑な仕様を検討する場合のテンプレート")
def test_specification_for_tiered_pricing():
    """
    仕様検討ポイント④：段階的な料金体系は必要か？
    - 例：最初の10単位まで10円、それ以降は8円など
    """
    usage_records = [{"user_id": "user1", "quantity": 15}]
    
    # 段階料金のルールを定義する必要がある
    pricing_rules = {
        "tiers": [
            {"up_to": 10, "unit_price": 10},
            {"up_to": "inf", "unit_price": 8},
        ]
    }

    # TODO: 期待される結果を仕様として定義する
    # 例: (10 * 10) + (5 * 8) = 140
    expected = 140 # 仮の期待値

    actual = charge_calculator.calculate_tiered(usage_records, pricing_rules)
    
    assert actual == expected, "段階料金の仕様を定義してください"

def test_specification_for_invalid_input():
    """
    仕様検討ポイント⑤：不正な入力（マイナスの利用量など）をどう処理するか？
    - 例：エラーを送出するべき
    """
    usage_records = [{"user_id": "user1", "quantity": -5}]
    unit_price = 10
    
    with pytest.raises(ValueError, match="利用量は負の値にできません"):
        charge_calculator.calculate(usage_records, unit_price)

