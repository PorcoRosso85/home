"""
Cypherクエリベースのガードレールルールテスト

このテストは新しいcypher_queryベースのガードレールルールの動作を検証します。
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path

# 親ディレクトリをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

import kuzu
from meta_node import MetaNode


class TestGuardrailCypherQuery:
    """Cypherクエリベースのガードレールルール機能のテスト"""

    @pytest.fixture
    def meta_node(self):
        """MetaNodeインスタンスを作成"""
        # 一時的なデータベースファイルを使用
        self.temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(self.temp_dir, "test.db")
        db = kuzu.Database(db_path)
        
        # テスト用のスキーマを作成
        conn = kuzu.Connection(db)
        conn.execute("CREATE NODE TABLE User(email STRING, age INT64, PRIMARY KEY(email))")
        conn.execute("CREATE NODE TABLE ValidationLog(rule_name STRING, timestamp INT64, passed BOOLEAN, PRIMARY KEY(rule_name))")
        
        yield MetaNode(db)
        # クリーンアップ
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_cypher_query_validation_rule(self, meta_node):
        """Cypherクエリベースのバリデーションルール"""
        # テストデータを作成
        conn = kuzu.Connection(meta_node.db)
        conn.execute("CREATE (:User {email: 'test@example.com', age: 25})")
        conn.execute("CREATE (:User {email: 'invalid-email', age: 30})")
        
        # Cypherクエリベースのバリデーションルールを作成
        rule_id = meta_node.create_guardrail_rule(
            rule_type="validation",
            name="email_validation_cypher",
            description="Cypherクエリでメールアドレスを検証",
            cypher_query="""
                MATCH (u:User {email: $email})
                WHERE u.email CONTAINS '@' AND u.email CONTAINS '.'
                RETURN true AS is_valid, 'Email format is valid' AS message
            """,
            priority=1,
            active=True
        )
        
        assert rule_id == "email_validation_cypher"
        
        # ルールを実行（有効なメール）
        result = meta_node.execute_guardrail_rules(
            data={"email": "test@example.com"}
        )
        assert result["passed"] is True
        assert len(result["executed_rules"]) == 1
        assert result["executed_rules"][0]["name"] == "email_validation_cypher"
        
        # ルールを実行（無効なメール）
        result2 = meta_node.execute_guardrail_rules(
            data={"email": "invalid-email"}
        )
        assert result2["passed"] is False
        assert len(result2["failed_rules"]) == 1
        assert result2["failed_rules"][0]["name"] == "email_validation_cypher"

    def test_cypher_query_transformation_rule(self, meta_node):
        """Cypherクエリベースの変換ルール"""
        # 変換ルールを作成（ログを記録）
        rule_id = meta_node.create_guardrail_rule(
            rule_type="transformation",
            name="log_validation_cypher",
            description="バリデーション結果をログに記録",
            cypher_query="""
                CREATE (:ValidationLog {
                    rule_name: $rule_name,
                    timestamp: $timestamp,
                    passed: $passed
                })
                RETURN true AS success, 'Validation logged' AS message
            """,
            priority=2,
            active=True
        )
        
        # ルールを実行
        import time
        result = meta_node.execute_guardrail_rules(
            data={
                "rule_name": "test_rule",
                "timestamp": int(time.time()),
                "passed": True
            }
        )
        
        assert result["passed"] is True
        assert len(result["executed_rules"]) == 1
        
        # ログが記録されたことを確認
        conn = kuzu.Connection(meta_node.db)
        log_result = conn.execute("MATCH (l:ValidationLog) RETURN l.rule_name")
        assert log_result.has_next()
        row = log_result.get_next()
        assert row[0] == "test_rule"

    def test_multiple_cypher_rules(self, meta_node):
        """複数のCypherクエリベースルールの実行"""
        # Cypherクエリベースのルール1
        meta_node.create_guardrail_rule(
            rule_type="validation",
            name="cypher_rule_1",
            description="Cypherクエリベースのルール1",
            cypher_query="""
                RETURN true AS passed, 'Cypher rule 1 executed' AS message
            """,
            priority=1,
            active=True
        )
        
        # Cypherクエリベースのルール2
        meta_node.create_guardrail_rule(
            rule_type="validation",
            name="cypher_rule_2",
            description="Cypherクエリベースのルール2",
            cypher_query="""
                RETURN true AS passed, 'Cypher rule 2 executed' AS message
            """,
            priority=2,
            active=True
        )
        
        # 両方のルールを実行
        result = meta_node.execute_guardrail_rules(data={})
        
        # デバッグ出力
        print(f"Result: {result}")
        print(f"Logs: {result['logs']}")
        
        assert result["passed"] is True
        assert len(result["executed_rules"]) == 2
        assert result["executed_rules"][0]["name"] == "cypher_rule_1"
        assert result["executed_rules"][1]["name"] == "cypher_rule_2"
        # ログに両方のメッセージが含まれていることを確認
        logs_str = " ".join(result["logs"])
        assert "Cypher rule 1 executed" in logs_str
        assert "Cypher rule 2 executed" in logs_str

    def test_cypher_query_with_parameters(self, meta_node):
        """パラメータを使用したCypherクエリ"""
        # 年齢チェックルールを作成
        meta_node.create_guardrail_rule(
            rule_type="validation",
            name="age_check_cypher",
            description="年齢制限をCypherクエリで確認",
            cypher_query="""
                WITH $age AS user_age, $min_age AS required_age
                WHERE user_age >= required_age
                RETURN true AS is_valid, 
                       'Age requirement met' AS message
            """,
            priority=1,
            active=True
        )
        
        # 年齢が条件を満たす場合
        result = meta_node.execute_guardrail_rules(
            data={"age": 25, "min_age": 18}
        )
        assert result["passed"] is True
        assert "Age requirement met" in " ".join(result["logs"])
        
        # 年齢が条件を満たさない場合
        result2 = meta_node.execute_guardrail_rules(
            data={"age": 15, "min_age": 18}
        )
        assert result2["passed"] is False
        assert len(result2["failed_rules"]) == 1