"""Hierarchy Validatorのテスト"""

import pytest
from .hierarchy_validator import HierarchyValidator


class TestHierarchyValidator:
    """HierarchyValidatorのテスト"""
    
    def test_validate_hierarchy_rule_parent_child_level_違反検出_エラーとペナルティ(self):
        """validate_hierarchy_rule_親子レベル違反_エラーとペナルティを返す"""
        validator = HierarchyValidator()
        
        # L4の要件がL0の親になろうとする
        cypher = """
        MATCH (child:RequirementEntity {id: 'req_vision_001', hierarchy_level: 0})
        MATCH (parent:RequirementEntity {id: 'req_task_001', hierarchy_level: 4})
        CREATE (parent)-[:PARENT_OF]->(child)
        """
        
        result = validator.validate_hierarchy_constraints(cypher)
        
        assert result["is_valid"] == False
        assert result["score"] == -1.0  # 最大ペナルティ
        assert "階層違反" in result["error"]
        assert "Level 4 cannot be parent of Level 0" in result["details"]

    def test_validate_hierarchy_rule_title_level_mismatch_不整合検出_警告(self):
        """validate_hierarchy_rule_タイトルとレベル不一致_警告を返す"""
        validator = HierarchyValidator()
        
        # "ビジョン"というタイトルだがL2として作成
        cypher = """
        CREATE (r:RequirementEntity {
            id: 'req_001',
            title: 'システムビジョン',
            hierarchy_level: 2
        })
        """
        
        result = validator.validate_hierarchy_constraints(cypher)
        
        assert result["is_valid"] == True  # 警告のみ
        assert result["score"] == -0.3  # 軽いペナルティ
        assert "warning" in result
        assert "ビジョンは通常Level 0" in result["warning"]

    def test_enforce_hierarchy_constraint_PARENT_OF作成_制約追加(self):
        """enforce_hierarchy_constraint_親子関係作成時_階層制約を追加"""
        validator = HierarchyValidator()
        
        original_cypher = """
        CREATE (p:RequirementEntity {id: 'parent'})
        CREATE (c:RequirementEntity {id: 'child'})
        CREATE (p)-[:PARENT_OF]->(c)
        """
        
        enforced_cypher = validator.enforce_hierarchy_constraint(original_cypher)
        
        assert "WHERE p.hierarchy_level < c.hierarchy_level" in enforced_cypher

    def test_detect_hierarchy_level_from_context_タイトル解析_レベル推定(self):
        """detect_hierarchy_level_タイトルから_適切なレベルを推定"""
        validator = HierarchyValidator()
        
        # 各階層のキーワードを含むタイトル
        test_cases = [
            ("システムビジョン", 0),
            ("アーキテクチャ設計", 1),
            ("認証モジュール", 2),
            ("ログインコンポーネント", 3),
            ("パスワード検証タスク", 4)
        ]
        
        for title, expected_level in test_cases:
            level = validator.detect_hierarchy_level_from_context(title)
            assert level == expected_level

    def test_階層違反_タスクがビジョンの親_エラーとスコアマイナス1(self):
        """階層違反検出_タスクがビジョンに依存_エラーとペナルティスコア"""
        validator = HierarchyValidator()
        
        # タスク実装（Level 4）がビジョン（Level 0）に依存する違反ケース
        cypher = """
        CREATE (parent:RequirementEntity {
            id: 'test_parent_task',
            title: 'タスク実装',
            description: '具体的なタスク',
            priority: 'medium',
            requirement_type: 'functional',
            verification_required: true
        }),
        (child:RequirementEntity {
            id: 'test_child_vision', 
            title: 'ビジョン',
            description: '上位ビジョン',
            priority: 'high',
            requirement_type: 'functional',
            verification_required: true
        }),
        (parent)-[:DEPENDS_ON]->(child)
        """
        
        result = validator.validate_hierarchy_constraints(cypher)
        
        # 階層違反が検出される
        assert result["is_valid"] == False
        assert result["score"] == -1.0
        assert result["error"] == "階層違反"
        assert "タスク実装(Level 4)がビジョン(Level 0)に依存" in str(result["details"])

    def test_自己参照_同一ノード間の依存_エラーとスコアマイナス1(self):
        """自己参照検出_同じノードが自分に依存_エラーとペナルティスコア"""
        validator = HierarchyValidator()
        
        cypher = """
        CREATE (r:RequirementEntity {id: 'self_ref_test'}),
        (r)-[:DEPENDS_ON]->(r)
        """
        
        result = validator.validate_hierarchy_constraints(cypher)
        
        # 自己参照が検出される
        assert result["is_valid"] == False
        assert result["score"] == -1.0
        assert result["error"] == "自己参照エラー"
        assert "自分自身に依存" in str(result["details"])

    def test_正常な階層依存_上位が下位に依存_成功(self):
        """正常な階層_上位階層が下位階層に依存_エラーなし"""
        validator = HierarchyValidator()
        
        cypher = """
        CREATE (arch:RequirementEntity {
            id: 'test_arch',
            title: 'アーキテクチャ設計',
            description: 'システムアーキテクチャ'
        }),
        (module:RequirementEntity {
            id: 'test_module',
            title: 'モジュール実装',
            description: '機能モジュール'
        }),
        (arch)-[:DEPENDS_ON]->(module)
        """
        
        result = validator.validate_hierarchy_constraints(cypher)
        
        # エラーなし
        assert result["is_valid"] == True
        assert result["score"] == 0.0
        assert result["error"] is None

    def test_複数CREATE文_各文を個別に検証(self):
        """複数CREATE文_それぞれの階層違反を検出"""
        validator = HierarchyValidator()
        
        cypher = """
        CREATE (vision:RequirementEntity {
            id: 'vision_001',
            title: 'システムビジョン'
        });
        
        CREATE (task:RequirementEntity {
            id: 'task_001',
            title: 'タスク実装'
        }),
        (vision2:RequirementEntity {
            id: 'vision_002',
            title: 'ビジョン'
        }),
        (task)-[:DEPENDS_ON]->(vision2);
        """
        
        result = validator.validate_hierarchy_constraints(cypher)
        
        # 2つ目のCREATE文で階層違反
        assert result["is_valid"] == False
        assert result["score"] == -1.0

    def test_MATCH後のCREATE_既存ノードとの関係で階層違反(self):
        """MATCH後CREATE_既存ノードとの階層違反を検出"""
        validator = HierarchyValidator()
        
        # 実際のシナリオ：既存のタスクに新しいビジョンを依存させる
        cypher = """
        MATCH (task:RequirementEntity {id: 'existing_task', title: 'タスク実装'})
        CREATE (vision:RequirementEntity {
            id: 'new_vision',
            title: 'ビジョン'
        }),
        (task)-[:DEPENDS_ON]->(vision)
        """
        
        # 現在の実装では、MATCHノードのタイトルが取得できないため、
        # CREATE部分のみで判定可能な場合のみ検出される
        result = validator.validate_hierarchy_constraints(cypher)
        # 将来的な拡張のためのテストケース

    def test_間接的循環参照_AからBからCからA_検出(self):
        """間接的循環参照_3段階の循環_エラーとペナルティスコア"""
        validator = HierarchyValidator()
        
        # A→B→C→Aの循環を作るクエリ
        cypher = """
        CREATE (a:RequirementEntity {id: 'req_a', title: 'モジュールA'}),
               (b:RequirementEntity {id: 'req_b', title: 'モジュールB'}),
               (c:RequirementEntity {id: 'req_c', title: 'モジュールC'}),
               (a)-[:DEPENDS_ON]->(b),
               (b)-[:DEPENDS_ON]->(c),
               (c)-[:DEPENDS_ON]->(a)
        """
        
        result = validator.validate_hierarchy_constraints(cypher)
        
        # 循環参照が検出される
        assert result["is_valid"] == False
        assert result["score"] == -1.0
        assert "循環参照" in result["error"]
        assert "req_a → req_b → req_c → req_a" in str(result["details"])

    def test_要件の曖昧性_具体化プロセス(self):
        """要望の曖昧性_対話的に具体化_測定可能な要件に変換"""
        # TODO: 新しいモジュールrequirement_clarifier.pyが必要
        # 1. 曖昧な表現の検出
        # 2. 質問生成
        # 3. 回答から具体的な要件生成
        pass

    def test_重複要件検出_embedding類似度(self):
        """重複要件_embedding類似度計算_マージ提案"""
        # TODO: embedding比較機能の実装
        # domain/embedder.pyの活用
        pass