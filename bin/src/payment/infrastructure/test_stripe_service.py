
import pytest
from unittest.mock import patch
from .stripe_service import StripePaymentGateway
from ..application.interfaces import PaymentGateway

def test_stripe_payment_gateway_charge():
    # 準備（Arrange）
    gateway: PaymentGateway = StripePaymentGateway()
    customer_id = "cus_12345"
    amount = 2000

    # モックの設定
    with patch('stripe.Charge.create') as mock_stripe_charge_create:
        mock_stripe_charge_create.return_value = {'status': 'succeeded'}

        # 実行（Act）
        success = gateway.charge(customer_id, amount)

        # 検証（Assert）
        assert success is True
        mock_stripe_charge_create.assert_called_once_with(
            customer=customer_id,
            amount=amount,
            currency='jpy'
        )
