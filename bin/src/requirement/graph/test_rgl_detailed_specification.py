"""
RGLシステム詳細仕様テスト
各コンポーネントが仕様に準拠しているかを個別に検証
"""
import pytest
import os
import re


class TestMainEntryPointSpecification:
    """main.pyが仕様に準拠しているか"""
    
    def test_mainは階層検証を使用していない(self):
        """
        仕様: main.pyはグラフ深さ制限を使用し、階層検証は使用しない
        """
        with open('main.py', 'r') as f:
            content = f.read()
        
        # 禁止されている階層関連の用語
        forbidden = [
            'hierarchy_validator',
            'hierarchy_result',
            '階層違反',
            'hierarchy_violation'
        ]
        
        violations = []
        for term in forbidden:
            if term in content:
                violations.append(term)
        
        assert len(violations) == 0, \
            f"main.pyに階層関連の用語が含まれています: {violations}"
    
    def test_mainはグラフベースの検証を使用する(self):
        """
        仕様: main.pyはグラフトラバーサルベースの検証を使用すべき
        """
        with open('main.py', 'r') as f:
            content = f.read()
        
        # 期待されるグラフ関連の用語
        expected_terms = [
            'graph_validator',
            'graph_depth',
            'path_length',
            'edge_traversal'
        ]
        
        found = []
        for term in expected_terms:
            if term in content:
                found.append(term)
        
        assert len(found) > 0, \
            "main.pyにグラフベースの検証が実装されていません"


class TestDomainLayerSpecification:
    """ドメイン層が仕様に準拠しているか"""
    
    def test_違反定義に階層違反が含まれていない(self):
        """
        仕様: 違反定義に階層違反は存在しない
        """
        violation_file = 'domain/violation_definitions.py'
        if os.path.exists(violation_file):
            with open(violation_file, 'r') as f:
                content = f.read()
            
            assert 'hierarchy_violation' not in content, \
                "違反定義に階層違反が含まれています（仕様違反）"
            assert '階層違反' not in content, \
                "違反定義に階層違反（日本語）が含まれています（仕様違反）"
    
    def test_スコアリングルールに階層関連ルールが含まれていない(self):
        """
        仕様: スコアリングルールは階層に依存しない
        """
        scoring_files = [
            'domain/scoring_rules.py',
            'domain/business_rules.py',
            'domain/friction_rules.py'
        ]
        
        violations = []
        for file_path in scoring_files:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                
                if 'hierarchy' in content.lower() or 'level' in content.lower():
                    violations.append(file_path)
        
        assert len(violations) == 0, \
            f"スコアリングルールに階層依存が含まれています: {violations}"


class TestInfrastructureLayerSpecification:
    """インフラ層が仕様に準拠しているか"""
    
    def test_グラフ深さ検証器が存在する(self):
        """
        仕様: graph_depth_validator.pyが存在すべき
        """
        expected_file = 'infrastructure/graph_depth_validator.py'
        assert os.path.exists(expected_file), \
            f"{expected_file}が存在しません（実装が必要）"
    
    def test_循環参照検出器が存在する(self):
        """
        仕様: circular_reference_detector.pyが存在すべき
        """
        expected_file = 'infrastructure/circular_reference_detector.py'
        assert os.path.exists(expected_file), \
            f"{expected_file}が存在しません（実装が必要）"
    
    def test_階層検証器は存在してはならない(self):
        """
        仕様: hierarchy_validator.pyは存在してはならない
        """
        forbidden_file = 'infrastructure/hierarchy_validator.py'
        assert not os.path.exists(forbidden_file), \
            f"{forbidden_file}が存在します（削除が必要）"


class TestApplicationLayerSpecification:
    """アプリケーション層が仕様に準拠しているか"""
    
    def test_スコアリングサービスは階層違反を扱わない(self):
        """
        仕様: スコアリングサービスは階層違反スコアを計算しない
        """
        scoring_service = 'application/scoring_service.py'
        if os.path.exists(scoring_service):
            with open(scoring_service, 'r') as f:
                content = f.read()
            
            forbidden_scores = [
                'hierarchy_violation',
                'hierarchy_skip',
                'level_mismatch',
                'title_level_mismatch'
            ]
            
            violations = []
            for score_type in forbidden_scores:
                if score_type in content:
                    violations.append(score_type)
            
            assert len(violations) == 0, \
                f"スコアリングサービスに階層関連スコアが含まれています: {violations}"


class TestCypherQuerySpecification:
    """Cypherクエリが仕様に準拠しているか"""
    
    def test_グラフ深さ制限クエリのテンプレートが存在する(self):
        """
        仕様: グラフ深さを計算するCypherテンプレートが存在すべき
        """
        # インフラ層のどこかにグラフ深さクエリがあるはず
        graph_queries = []
        
        for root, dirs, files in os.walk('infrastructure'):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        if 'shortestPath' in content or 'length(path)' in content:
                            graph_queries.append(file_path)
                    except:
                        pass
        
        assert len(graph_queries) > 0, \
            "グラフ深さを計算するCypherクエリが見つかりません（実装が必要）"
    
    def test_循環参照検出クエリのテンプレートが存在する(self):
        """
        仕様: 循環参照を検出するCypherテンプレートが存在すべき
        """
        circular_queries = []
        
        for root, dirs, files in os.walk('.'):
            if '.venv' in root or '__pycache__' in root:
                continue
            
            for file in files:
                if file.endswith(('.py', '.cypher')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        # 循環参照検出のパターン
                        if re.search(r'\((\w+)\).*-\[.*\*.*\].*-.*>\s*\(\1\)', content):
                            circular_queries.append(file_path)
                    except:
                        pass
        
        assert len(circular_queries) > 0, \
            "循環参照を検出するCypherクエリが見つかりません（実装が必要）"