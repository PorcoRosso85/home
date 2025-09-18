"""
ガードレール＆ワークフローテスト（Cypherクエリベース版）

このテストは以下を検証します：
1. Cypherクエリベースのガードレールルールの作成と実行
2. 優先度順でのルール実行（priority順）  
3. activeフラグによるルールの有効/無効切り替え
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


class TestGuardrailWorkflowCypher:
    """Cypherベースのガードレール＆ワークフロー機能のテスト"""

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
            CREATE NODE TABLE Email(
                id INT64,
                address STRING,
                PRIMARY KEY(id)
            )
        """)
        
        yield meta_node
        
        # クリーンアップ
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_create_validation_rule(self, meta_node):
        """Cypherクエリベースのガードレールルール（rule_type="validation"）の作成と実行"""
        # バリデーションルールを作成
        rule_id = meta_node.create_guardrail_rule(
            rule_type="validation",
            name="email_format_check",
            description="メールアドレスの形式をチェック",
            cypher_query="""
                WITH $email AS email
                RETURN 
                    CASE WHEN email CONTAINS '@' AND email CONTAINS '.' 
                         THEN true 
                         ELSE false 
                    END AS is_valid,
                    CASE WHEN email CONTAINS '@' AND email CONTAINS '.' 
                         THEN 'Email format is valid' 
                         ELSE 'Invalid email format' 
                    END AS message
            """,
            priority=1,
            active=True
        )
        
        assert rule_id is not None
        
        # ルールを実行（有効なメール）
        result = meta_node.execute_guardrail_rules(
            data={"email": "test@example.com"}
        )
        assert result["passed"] is True
        assert len(result["executed_rules"]) == 1
        
        # ルールを実行（無効なメール）
        result = meta_node.execute_guardrail_rules(
            data={"email": "invalid-email"}
        )
        assert result["passed"] is False
        assert len(result["failed_rules"]) == 1

    def test_rule_execution_by_priority(self, meta_node):
        """優先度順でのルール実行（priority順）"""
        # 優先度の異なる複数のルールを作成
        rule1_id = meta_node.create_guardrail_rule(
            rule_type="logging",
            name="high_priority_rule",
            description="高優先度ルール",
            cypher_query="RETURN true AS success, 'High priority executed' AS message",
            priority=1,  # 高優先度
            active=True
        )
        
        rule2_id = meta_node.create_guardrail_rule(
            rule_type="logging", 
            name="low_priority_rule",
            description="低優先度ルール",
            cypher_query="RETURN true AS success, 'Low priority executed' AS message",
            priority=10,  # 低優先度
            active=True
        )
        
        rule3_id = meta_node.create_guardrail_rule(
            rule_type="logging",
            name="medium_priority_rule", 
            description="中優先度ルール",
            cypher_query="RETURN true AS success, 'Medium priority executed' AS message",
            priority=5,  # 中優先度
            active=True
        )
        
        # ルールを実行
        result = meta_node.execute_guardrail_rules(data={})
        
        # 実行順序を確認（priority順: 1 -> 5 -> 10）
        assert len(result["executed_rules"]) == 3
        assert result["executed_rules"][0]["name"] == "high_priority_rule"
        assert result["executed_rules"][1]["name"] == "medium_priority_rule"
        assert result["executed_rules"][2]["name"] == "low_priority_rule"
        
        # 実行ログを確認
        assert any("High priority executed" in log for log in result["logs"])
        assert any("Medium priority executed" in log for log in result["logs"])
        assert any("Low priority executed" in log for log in result["logs"])

    def test_active_flag_toggle(self, meta_node):
        """activeフラグによるルールの有効/無効切り替え"""
        # アクティブなルールを作成
        active_rule_id = meta_node.create_guardrail_rule(
            rule_type="logging",
            name="active_rule",
            description="アクティブなルール",
            cypher_query="RETURN true AS success, 'Active rule executed' AS message",
            priority=1,
            active=True
        )
        
        # 非アクティブなルールを作成
        inactive_rule_id = meta_node.create_guardrail_rule(
            rule_type="logging",
            name="inactive_rule",
            description="非アクティブなルール",
            cypher_query="RETURN true AS success, 'Inactive rule executed' AS message",
            priority=2,
            active=False
        )
        
        # ルールを実行
        result = meta_node.execute_guardrail_rules(data={})
        
        # アクティブなルールのみが実行されることを確認
        assert len(result["executed_rules"]) == 1
        assert result["executed_rules"][0]["name"] == "active_rule"
        assert any("Active rule executed" in log for log in result["logs"])
        assert not any("Inactive rule executed" in log for log in result["logs"])
        
        # ルールのアクティブ状態を切り替え
        meta_node.update_guardrail_rule(inactive_rule_id, active=True)
        meta_node.update_guardrail_rule(active_rule_id, active=False)
        
        # 再度実行
        result2 = meta_node.execute_guardrail_rules(data={})
        
        # 切り替え後の実行結果を確認
        assert len(result2["executed_rules"]) == 1
        assert result2["executed_rules"][0]["name"] == "inactive_rule"
        assert any("Inactive rule executed" in log for log in result2["logs"])
        assert not any("Active rule executed" in log for log in result2["logs"])