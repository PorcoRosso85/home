#!/usr/bin/env python3
"""
出力例の確認
"""
from . import log


# 基本的な使用例
print("=== 出力例 ===")
log("INFO", {"uri": "/api/users", "message": "User created", "user_id": "123"})

# 出力例:
# {"level":"INFO","uri":"/api/users","message":"User created","user_id":"123"}


# エラーログ
log("ERROR", {"uri": "/api/payment", "message": "Payment failed", "amount": 1000, "error": "insufficient_funds"})

# 出力例:
# {"level":"ERROR","uri":"/api/payment","message":"Payment failed","amount":1000,"error":"insufficient_funds"}