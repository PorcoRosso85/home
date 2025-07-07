
import pytest
from .models import Billing, Customer, Usage
from .services import calculate_billing_amount

def test_calculate_billing_amount_standard_plan():
    # 準備（Arrange）
    customer = Customer(id="cust_1", plan="standard")
    usage = Usage(user_id="cust_1", minutes=100)

    # 実行（Act）
    billing = calculate_billing_amount(customer, usage)

    # 検証（Assert）
    assert isinstance(billing, Billing)
    assert billing.amount == 1000  # 仮: standardプランは 10円/分

def test_calculate_billing_amount_premium_plan():
    # 準備（Arrange）
    customer = Customer(id="cust_2", plan="premium")
    usage = Usage(user_id="cust_2", minutes=100)

    # 実行（Act）
    billing = calculate_billing_amount(customer, usage)

    # 検証（Assert）
    assert isinstance(billing, Billing)
    assert billing.amount == 800  # 仮: premiumプランは 8円/分

def test_billing_for_zero_usage_is_zero():
    # 準備（Arrange）
    customer = Customer(id="cust_3", plan="standard")
    usage = Usage(user_id="cust_3", minutes=0)

    # 実行（Act）
    billing = calculate_billing_amount(customer, usage)

    # 検証（Assert）
    assert billing.amount == 0

def test_billing_for_negative_usage_is_zero():
    # 準備（Arrange）
    customer = Customer(id="cust_4", plan="standard")
    usage = Usage(user_id="cust_4", minutes=-50)

    # 実行（Act）
    billing = calculate_billing_amount(customer, usage)

    # 検証（Assert）
    assert billing.amount == 0

def test_error_on_missing_plan():
    # 準備（Arrange）
    # plan情報が欠落したCustomerオブジェクト
    customer_without_plan = Customer(id="cust_5", plan=None)
    usage = Usage(user_id="cust_5", minutes=100)

    # 実行（Act） & 検証（Assert）
    # エラーを値として返すことを期待
    result = calculate_billing_amount(customer_without_plan, usage)
    assert isinstance(result, Error) # Errorはカスタムエラー型を想定
    assert result.message == "Customer plan is not defined."
