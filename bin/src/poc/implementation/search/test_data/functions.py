"""Functions test file"""


def simple_function():
    """シンプルな関数"""
    pass


def function_with_args(x: int, y: int) -> int:
    """引数付き関数"""
    return x + y


async def async_function():
    """非同期関数"""
    await some_operation()


def nested_function():
    """ネストした関数"""
    def inner_function():
        return "inner"
    return inner_function()


# ラムダ式
lambda_func = lambda x: x * 2