#!/usr/bin/env python3
"""
出力例の確認
"""
from typing import TypedDict
from . import log, LogData


# 基本的な使用例（LogData準拠）
print("=== 基本的な使用例 ===")
log("INFO", {"uri": "/api/users", "message": "User created", "user_id": "123"})

# 出力例:
# {"level":"INFO","uri":"/api/users","message":"User created","user_id":"123"}


# 型定義の拡張例
class MyAppLogData(LogData):
    """アプリケーション固有の拡張型"""
    user_id: str
    amount: int
    error: str


# 拡張型を使った例
print("\n=== 拡張型の使用例 ===")
log_data: MyAppLogData = {
    "uri": "/api/payment",
    "message": "Payment failed",
    "amount": 1000,
    "error": "insufficient_funds",
    "user_id": "user456"
}
log("ERROR", log_data)

# 出力例:
# {"level":"ERROR","uri":"/api/payment","message":"Payment failed","amount":1000,"error":"insufficient_funds","user_id":"user456"}