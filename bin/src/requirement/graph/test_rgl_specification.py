"""
RGLシステム仕様テスト
仕様: 階層概念は存在しない。グラフのエッジ関係深さの制限のみ。
"""
import pytest
import os
import re


class TestRGLSpecification:
    """RGLシステムの正しい仕様を定義するテスト"""
    
    def test_スキーマに階層関連プロパティが存在しないこと(self):
        """
        仕様: RequirementEntityテーブルにlevel, hierarchy_levelなどの
        階層を示すプロパティは存在してはならない
        """
        schema_path = os.path.join(
            os.path.dirname(__file__), 
            "ddl", 
            "schema.cypher"
        )
        
        with open(schema_path, 'r') as f:
            schema_content = f.read()
        
        # 禁止されているプロパティ
        forbidden_properties = [
            'level',
            'hierarchy_level',
            'layer',
            'tier',
            'depth'  # グラフのdepthとは異なる、固定的なdepthプロパティ
        ]
        
        for prop in forbidden_properties:
            assert prop not in schema_content.lower(), \
                f"スキーマに階層プロパティ'{prop}'が含まれています（仕様違反）"
    
    def test_階層を前提とした検証ロジックが存在しないこと(self):
        """
        仕様: 階層違反、レベル違反などの概念に基づく検証は存在してはならない
        """
        # hierarchy_validatorのようなファイルの存在をチェック
        forbidden_files = [
            'infrastructure/hierarchy_validator.py',
            'domain/hierarchy_rules.py',
            'infrastructure/hierarchy_udfs.py',
            'domain/requirement_hierarchy.py'
        ]
        
        existing_forbidden_files = []
        for file_path in forbidden_files:
            if os.path.exists(file_path):
                existing_forbidden_files.append(file_path)
        
        assert len(existing_forbidden_files) == 0, \
            f"階層を前提としたファイルが存在します（仕様違反）: {existing_forbidden_files}"
    
    def test_コード内で固定レベル値を使用していないこと(self):
        """
        仕様: 0=vision, 4=taskのような固定的なレベル定義は存在してはならない
        """
        level_definitions = []
        
        for root, dirs, files in os.walk('.'):
            if '.venv' in root or '__pycache__' in root or '.git' in root:
                continue
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        # テストファイル自身は除外
                        if 'test_rgl_specification.py' in file_path:
                            continue
                        
                        # 固定レベル定義のパターン
                        if re.search(r'vision.*=.*0|0.*:.*vision', content, re.IGNORECASE):
                            level_definitions.append((file_path, 'vision=0'))
                        if re.search(r'task.*=.*4|4.*:.*task', content, re.IGNORECASE):
                            level_definitions.append((file_path, 'task=4'))
                        if re.search(r'LEVELS\s*=\s*{', content):
                            level_definitions.append((file_path, 'LEVELS定義'))
                    except:
                        pass
        
        assert len(level_definitions) == 0, \
            f"固定レベル定義が存在します（仕様違反）: {level_definitions[:5]}"
    
    def test_要件間の制約はグラフトラバーサルで判定されること(self):
        """
        仕様: 要件間の関係制約は、グラフのエッジをトラバースして判定される
        """
        # グラフトラバーサルを使用している検証ロジックを探す
        graph_based_validation = []
        
        validation_patterns = [
            r'shortestPath',
            r'MATCH.*path.*=',
            r'length\(path\)',
            r'graph.*depth',
            r'traverse'
        ]
        
        for root, dirs, files in os.walk('.'):
            if '.venv' in root or '__pycache__' in root or '.git' in root:
                continue
            
            for file in files:
                if file.endswith('.py') and 'validat' in file.lower():
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        for pattern in validation_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                graph_based_validation.append(file_path)
                                break
                    except:
                        pass
        
        # 現在の実装はグラフベースではないはず
        assert len(graph_based_validation) > 0, \
            "グラフトラバーサルベースの検証が見つかりません（実装が必要）"
    
    def test_エラーメッセージに階層違反という用語を使用していないこと(self):
        """
        仕様: エラーメッセージは「階層違反」ではなく、
        「グラフ深さ制限」や「循環参照」などの用語を使用する
        """
        hierarchy_error_messages = []
        
        forbidden_terms = [
            '階層違反',
            'hierarchy violation',
            'level violation',
            'レベル違反',
            'level mismatch',
            'hierarchy mismatch'
        ]
        
        for root, dirs, files in os.walk('.'):
            if '.venv' in root or '__pycache__' in root or '.git' in root:
                continue
            
            for file in files:
                if file.endswith(('.py', '.md')):
                    file_path = os.path.join(root, file)
                    try:
                        # テストファイル自身は除外
                        if 'test_rgl_specification.py' in file_path:
                            continue
                            
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        for term in forbidden_terms:
                            if term in content.lower():
                                hierarchy_error_messages.append((file_path, term))
                                break
                    except:
                        pass
        
        assert len(hierarchy_error_messages) == 0, \
            f"階層違反用語を使用しているファイル（仕様違反）: {hierarchy_error_messages[:5]}"
    
    def test_要件IDに階層的な命名規則を強制していないこと(self):
        """
        仕様: req_vision_xxx, req_task_xxxのような階層的命名は
        単なる例であり、システムは特別扱いしない
        """
        hierarchical_id_enforcement = []
        
        patterns = [
            r'req_vision_.*必須',
            r'req_task_.*必須',
            r'id.*must.*start.*with.*req_(vision|task)',
            r'if.*startswith.*req_(vision|task)',
            r'infer.*level.*from.*id'
        ]
        
        for root, dirs, files in os.walk('.'):
            if '.venv' in root or '__pycache__' in root or '.git' in root:
                continue
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        # テストファイル自身は除外
                        if 'test_rgl_specification.py' in file_path:
                            continue
                            
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        for pattern in patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                hierarchical_id_enforcement.append(file_path)
                                break
                    except:
                        pass
        
        assert len(hierarchical_id_enforcement) == 0, \
            f"階層的ID命名を強制しているファイル（仕様違反）: {hierarchical_id_enforcement}"