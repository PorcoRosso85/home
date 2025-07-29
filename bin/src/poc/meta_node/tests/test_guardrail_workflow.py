"""
ガードレール＆ワークフローテスト

このテストは以下を検証します：
1. ガードレールルール（rule_type="validation"）の作成と実行
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


class TestGuardrailWorkflow:
    """ガードレール＆ワークフロー機能のテスト"""

    @pytest.fixture
    def meta_node(self):
        """MetaNodeインスタンスを作成"""
        # 一時的なデータベースファイルを使用
        self.temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(self.temp_dir, "test.db")
        db = kuzu.Database(db_path)
        yield MetaNode(db)
        # クリーンアップ
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_create_validation_rule(self, meta_node):
        """ガードレールルール（rule_type="validation"）の作成と実行"""
        # バリデーションルールを作成
        rule_id = meta_node.create_guardrail_rule(
            rule_type="validation",
            name="email_format_check",
            description="メールアドレスの形式をチェック",
            condition="'email' in data and data.get('email')",
            action="raise_error(ValueError('Invalid email format')) if '@' not in data.get('email', '') else 'pass'",
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
        with pytest.raises(ValueError, match="Invalid email format"):
            meta_node.execute_guardrail_rules(
                data={"email": "invalid-email"}
            )

    def test_rule_execution_by_priority(self, meta_node):
        """優先度順でのルール実行（priority順）"""
        # 優先度の異なる複数のルールを作成
        rule1_id = meta_node.create_guardrail_rule(
            rule_type="validation",
            name="high_priority_rule",
            description="高優先度ルール",
            condition="True",
            action="log('High priority executed')",
            priority=1,  # 高優先度
            active=True
        )
        
        rule2_id = meta_node.create_guardrail_rule(
            rule_type="validation", 
            name="low_priority_rule",
            description="低優先度ルール",
            condition="True",
            action="log('Low priority executed')",
            priority=10,  # 低優先度
            active=True
        )
        
        rule3_id = meta_node.create_guardrail_rule(
            rule_type="validation",
            name="medium_priority_rule", 
            description="中優先度ルール",
            condition="True",
            action="log('Medium priority executed')",
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
        assert result["logs"][0] == "High priority executed"
        assert result["logs"][1] == "Medium priority executed"
        assert result["logs"][2] == "Low priority executed"

    def test_active_flag_toggle(self, meta_node):
        """activeフラグによるルールの有効/無効切り替え"""
        # アクティブなルールを作成
        active_rule_id = meta_node.create_guardrail_rule(
            rule_type="validation",
            name="active_rule",
            description="アクティブなルール",
            condition="True",
            action="log('Active rule executed')",
            priority=1,
            active=True
        )
        
        # 非アクティブなルールを作成
        inactive_rule_id = meta_node.create_guardrail_rule(
            rule_type="validation",
            name="inactive_rule",
            description="非アクティブなルール",
            condition="True",
            action="log('Inactive rule executed')",
            priority=2,
            active=False
        )
        
        # ルールを実行
        result = meta_node.execute_guardrail_rules(data={})
        
        # アクティブなルールのみが実行されることを確認
        assert len(result["executed_rules"]) == 1
        assert result["executed_rules"][0]["name"] == "active_rule"
        assert "Active rule executed" in result["logs"]
        assert "Inactive rule executed" not in result["logs"]
        
        # ルールのアクティブ状態を切り替え
        meta_node.update_guardrail_rule(inactive_rule_id, active=True)
        meta_node.update_guardrail_rule(active_rule_id, active=False)
        
        # 再度実行
        result2 = meta_node.execute_guardrail_rules(data={})
        
        # 切り替え後の実行結果を確認
        assert len(result2["executed_rules"]) == 1
        assert result2["executed_rules"][0]["name"] == "inactive_rule"
        assert "Inactive rule executed" in result2["logs"]
        assert "Active rule executed" not in result2["logs"]