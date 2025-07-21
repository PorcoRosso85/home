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


def test_simple_echo_contract():
    """最も単純なecho契約をテストできること"""
    from contract_e2e import run_contract_tests
    
    # Given: 単純なecho契約のスキーマ
    input_schema = {
        "type": "object",
        "properties": {
            "message": {"type": "string"}
        },
        "required": ["message"]
    }
    
    output_schema = {
        "type": "object", 
        "properties": {
            "echo": {"type": "string"}
        },
        "required": ["echo"]
    }
    
    # When: echoプログラムに対してテストを実行
    result = run_contract_tests(
        executable='echo \'{"echo": "test"}\'',
        input_schema=input_schema,
        output_schema=output_schema,
        test_count=1  # Baby Steps: 最初は1回だけ
    )
    
    # Then: テストが成功すること
    assert result["ok"] is True
    assert result["report"]["passed"] == 1
    assert result["report"]["failed"] == 0


def test_schema_based_data_generation():
    """JSON Schemaから自動的にテストデータが生成されること"""
    from contract_e2e import run_contract_tests
    
    # Given: より複雑なスキーマ
    input_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0, "maximum": 150}
        },
        "required": ["name", "age"]
    }
    
    output_schema = {
        "type": "object",
        "properties": {
            "greeting": {"type": "string"}
        },
        "required": ["greeting"]
    }
    
    # 入力を受け取って挨拶を返すシンプルなプログラム
    executable = '''python -c "
import json
import sys
data = json.load(sys.stdin)
print(json.dumps({'greeting': f'Hello {data[\\"name\\"]}, age {data[\\"age\\"]}'}))
"'''
    
    # When: スキーマベースでテストを実行
    result = run_contract_tests(
        executable=executable,
        input_schema=input_schema,
        output_schema=output_schema,
        test_count=1
    )
    
    # Then: 
    # - スキーマから自動生成されたデータでテストが実行される
    # - 入力がスキーマに準拠している
    # - 出力がスキーマに準拠している
    
    # デバッグ情報を出力
    if not result["ok"]:
        print(f"Result: {result}")
        if result["test_cases"]:
            print(f"Test case: {result['test_cases'][0]}")
    
    assert result["ok"] is True
    assert result["report"]["passed"] == 1
    assert result["report"]["failed"] == 0
    
    # 生成されたテストデータの情報が含まれていること
    assert "test_cases" in result
    assert len(result["test_cases"]) == 1
    test_case = result["test_cases"][0]
    assert "input" in test_case
    assert "name" in test_case["input"]
    assert "age" in test_case["input"]
    assert isinstance(test_case["input"]["name"], str)
    assert isinstance(test_case["input"]["age"], int)
    assert 0 <= test_case["input"]["age"] <= 150