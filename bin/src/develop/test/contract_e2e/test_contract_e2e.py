"""Contract E2E Testing Framework Tests

規約に従い、公開APIの振る舞いのみをテストする。
リファクタリングの壁の原則：実装詳細に依存しない。
"""


def test_framework_can_be_imported():
    """フレームワークがインポート可能であること"""
    import contract_e2e
    assert contract_e2e is not None


def test_public_api_exists():
    """公開APIが存在すること"""
    from contract_e2e import run_contract_tests
    assert callable(run_contract_tests)