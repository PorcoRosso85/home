
import pytest
from unittest.mock import Mock
from .services import create_charge_for_user
from .interfaces import PaymentGateway
from ..domain.models import Customer, Usage

def test_create_charge_for_user():
    # 準備（Arrange）
    user_id = "user_123"
    mock_payment_gateway = Mock(spec=PaymentGateway)
    mock_payment_gateway.charge.return_value = True

    # 実行（Act）
    success = create_charge_for_user(user_id, mock_payment_gateway)

    # 検証（Assert）
    assert success is True
    mock_payment_gateway.charge.assert_called_once()
