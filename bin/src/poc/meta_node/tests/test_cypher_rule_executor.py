"""
Cypherベースのガードレールルール実行テスト

このテストは以下を検証します：
1. Cypherクエリベースのルール実行
2. pass/fail判定ロジック
3. エラーハンドリング
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


class TestCypherRuleExecutor:
    """CypherベースのRuleExecutorのテスト"""

    @pytest.fixture
    def meta_node(self):
        """MetaNodeインスタンスを作成"""
        # 一時的なデータベースファイルを使用
        self.temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(self.temp_dir, "test.db")
        db = kuzu.Database(db_path)
        meta_node = MetaNode(db)
        
        # テスト用のデータを準備
        conn = kuzu.Connection(db)
        conn.execute("""
            CREATE NODE TABLE User(
                id INT64,
                email STRING,
                age INT64,
                PRIMARY KEY(id)
            )
        """)
        conn.execute("CREATE (:User {id: 1, email: 'test@example.com', age: 25})")
        conn.execute("CREATE (:User {id: 2, email: 'invalid-email', age: 17})")
        
        yield meta_node
        
        # クリーンアップ
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_cypher_validation_rule_pass(self, meta_node):
        """Cypherクエリでのバリデーションルール（成功）"""
        # メールアドレス形式をチェックするCypherクエリルール
        rule_id = meta_node.create_guardrail_rule(
            rule_type="validation",
            name="email_validation",
            description="メールアドレスの形式をCypherでチェック",
            cypher_query="""
                MATCH (u:User {id: $user_id})
                RETURN u.email CONTAINS '@' AS is_valid, 
                       CASE WHEN u.email CONTAINS '@' 
                            THEN 'Email format is valid' 
                            ELSE 'Invalid email format' 
                       END AS message
            """,
            priority=1,
            active=True
        )
        
        # ルールを実行（有効なメール）
        result = meta_node.execute_guardrail_rules(
            data={"user_id": 1}
        )
        
        assert result["passed"] is True
        assert len(result["executed_rules"]) == 1
        assert result["executed_rules"][0]["name"] == "email_validation"
        assert "[email_validation] Email format is valid" in result["logs"]

    def test_cypher_validation_rule_fail(self, meta_node):
        """Cypherクエリでのバリデーションルール（失敗）"""
        # メールアドレス形式をチェックするCypherクエリルール
        rule_id = meta_node.create_guardrail_rule(
            rule_type="validation",
            name="email_validation",
            description="メールアドレスの形式をCypherでチェック",
            cypher_query="""
                MATCH (u:User {id: $user_id})
                RETURN u.email CONTAINS '@' AS is_valid,
                       CASE WHEN u.email CONTAINS '@' 
                            THEN 'Email format is valid' 
                            ELSE 'Invalid email format' 
                       END AS message
            """,
            priority=1,
            active=True
        )
        
        # ルールを実行（無効なメール）
        result = meta_node.execute_guardrail_rules(
            data={"user_id": 2}
        )
        
        assert result["passed"] is False
        assert len(result["failed_rules"]) == 1
        assert result["failed_rules"][0]["name"] == "email_validation"
        assert "[email_validation] Invalid email format" in result["logs"]

    def test_age_verification_rule(self, meta_node):
        """年齢確認ルールのテスト"""
        # 年齢が18歳以上かチェックするルール
        rule_id = meta_node.create_guardrail_rule(
            rule_type="validation",
            name="age_verification",
            description="年齢が18歳以上かチェック",
            cypher_query="""
                MATCH (u:User {id: $user_id})
                RETURN u.age >= 18 AS is_adult,
                       CASE WHEN u.age >= 18 
                            THEN 'User is an adult' 
                            ELSE 'User is under 18' 
                       END AS message
            """,
            priority=2,
            active=True
        )
        
        # 成人の場合
        result = meta_node.execute_guardrail_rules(
            data={"user_id": 1}
        )
        assert result["passed"] is True
        assert any(r["name"] == "age_verification" for r in result["executed_rules"])
        
        # 未成年の場合
        result = meta_node.execute_guardrail_rules(
            data={"user_id": 2}
        )
        assert result["passed"] is False
        assert any(r["name"] == "age_verification" for r in result["failed_rules"])

    def test_multiple_rules_priority_order(self, meta_node):
        """複数ルールの優先度順実行"""
        # 優先度1のルール（最初に実行される）
        meta_node.create_guardrail_rule(
            rule_type="logging",
            name="log_access",
            description="アクセスログを記録",
            cypher_query="RETURN true AS success, 'Access logged' AS message",
            priority=1,
            active=True
        )
        
        # 優先度2のルール
        meta_node.create_guardrail_rule(
            rule_type="validation",
            name="user_exists",
            description="ユーザーの存在チェック",
            cypher_query="""
                MATCH (u:User {id: $user_id})
                RETURN COUNT(u) > 0 AS user_exists,
                       CASE WHEN COUNT(u) > 0 
                            THEN 'User found' 
                            ELSE 'User not found' 
                       END AS message
            """,
            priority=2,
            active=True
        )
        
        result = meta_node.execute_guardrail_rules(
            data={"user_id": 1}
        )
        
        assert result["passed"] is True
        assert len(result["executed_rules"]) == 2
        # 優先度順に実行されることを確認
        assert result["executed_rules"][0]["name"] == "log_access"
        assert result["executed_rules"][1]["name"] == "user_exists"

    def test_empty_cypher_query_skip(self, meta_node):
        """空のCypherクエリはスキップされる"""
        rule_id = meta_node.create_guardrail_rule(
            rule_type="validation",
            name="empty_rule",
            description="空のクエリルール",
            cypher_query="",  # 空のクエリ
            priority=1,
            active=True
        )
        
        result = meta_node.execute_guardrail_rules(data={})
        
        assert result["passed"] is True
        assert len(result["executed_rules"]) == 0
        assert "Rule 'empty_rule' has no cypher_query or condition/action. Skipping." in result["logs"]

    def test_cypher_syntax_error_handling(self, meta_node):
        """Cypher構文エラーのハンドリング"""
        rule_id = meta_node.create_guardrail_rule(
            rule_type="validation",
            name="syntax_error_rule",
            description="構文エラーのあるルール",
            cypher_query="INVALID CYPHER SYNTAX",  # 無効なCypher
            priority=1,
            active=True
        )
        
        result = meta_node.execute_guardrail_rules(data={})
        
        assert result["passed"] is False
        assert len(result["failed_rules"]) == 1
        assert result["failed_rules"][0]["name"] == "syntax_error_rule"
        assert "error" in result["failed_rules"][0]
        assert any("Error executing" in log for log in result["logs"])

    def test_validation_rule_stops_on_failure(self, meta_node):
        """validationタイプのルールが失敗したら後続ルールは実行されない"""
        # 優先度1: 必ず失敗するvalidationルール
        meta_node.create_guardrail_rule(
            rule_type="validation",
            name="always_fail",
            description="必ず失敗するルール",
            cypher_query="RETURN false AS result, 'This rule always fails' AS message",
            priority=1,
            active=True
        )
        
        # 優先度2: このルールは実行されないはず
        meta_node.create_guardrail_rule(
            rule_type="logging",
            name="should_not_run",
            description="実行されないはずのルール",
            cypher_query="RETURN true AS result, 'This should not run' AS message",
            priority=2,
            active=True
        )
        
        result = meta_node.execute_guardrail_rules(data={})
        
        assert result["passed"] is False
        assert len(result["failed_rules"]) == 1
        assert result["failed_rules"][0]["name"] == "always_fail"
        assert len(result["executed_rules"]) == 0
        assert "Validation rule 'always_fail' failed. Stopping execution." in result["logs"]
        assert not any("This should not run" in log for log in result["logs"])

    def test_numeric_result_interpretation(self, meta_node):
        """数値結果の解釈テスト"""
        # 0は失敗、それ以外は成功として解釈
        meta_node.create_guardrail_rule(
            rule_type="validation",
            name="count_check",
            description="カウントチェック",
            cypher_query="""
                MATCH (u:User)
                WHERE u.age >= $min_age
                RETURN COUNT(u) AS count
            """,
            priority=1,
            active=True
        )
        
        # 条件を満たすユーザーが存在する場合（成功）
        result = meta_node.execute_guardrail_rules(
            data={"min_age": 20}
        )
        assert result["passed"] is True
        
        # 条件を満たすユーザーが存在しない場合（失敗）
        result = meta_node.execute_guardrail_rules(
            data={"min_age": 30}
        )
        assert result["passed"] is False

    def test_string_result_interpretation(self, meta_node):
        """文字列結果の解釈テスト"""
        # 特定の文字列を成功として解釈
        for success_value in ['true', 'pass', 'ok', 'yes', '1']:
            meta_node.create_guardrail_rule(
                rule_type="validation",
                name=f"string_test_{success_value}",
                description=f"文字列結果テスト: {success_value}",
                cypher_query=f"RETURN '{success_value}' AS result",
                priority=1,
                active=True
            )
            
            result = meta_node.execute_guardrail_rules(data={})
            assert result["passed"] is True
            
            # ルールを削除（次のテストのため）
            conn = kuzu.Connection(meta_node.db)
            conn.execute(f"MATCH (r:GuardrailRule {{name: 'string_test_{success_value}'}}) DELETE r")