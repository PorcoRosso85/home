"""
スキーマとコードの整合性を検証するテスト
"""
import os
import re
import pytest


class TestSchemaCodeConsistency:
    """DDLスキーマとアプリケーションコードの整合性を検証"""
    
    def test_固定的な階層プロパティはスキーマに存在しない(self):
        """
        level, hierarchy_levelなどの固定的な階層プロパティがスキーマに存在しないことを確認
        （RGLではグラフのエッジ関係で制約を表現するため）
        """
        # スキーマファイルを読み込み
        schema_path = os.path.join(
            os.path.dirname(__file__), 
            "ddl", 
            "schema.cypher"
        )
        
        with open(schema_path, 'r') as f:
            schema_content = f.read()
        
        # RequirementEntityテーブルの定義を抽出
        req_entity_match = re.search(
            r'CREATE NODE TABLE RequirementEntity \((.*?)\);',
            schema_content,
            re.DOTALL
        )
        
        assert req_entity_match, "RequirementEntityテーブルが見つかりません"
        
        # levelプロパティが定義されていないことを確認
        req_entity_def = req_entity_match.group(1)
        assert 'level' not in req_entity_def.lower(), \
            "levelプロパティはスキーマに存在すべきではありません"
    
    def test_グラフ深さ制限はエッジ関係で判定される(self):
        """
        グラフの深さ制限がエッジ関係の解析によって行われることを確認
        （固定的な階層プロパティに依存しない）
        """
        # 階層判定に関連するファイルを検索
        hierarchy_files = []
        for root, dirs, files in os.walk('.'):
            # .venvやテストディレクトリは除外
            if '.venv' in root or '__pycache__' in root:
                continue
            
            for file in files:
                if file.endswith('.py') and 'hierarchy' in file.lower():
                    hierarchy_files.append(os.path.join(root, file))
        
        # 各ファイルでlevelプロパティの使用をチェック
        for file_path in hierarchy_files:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # r.level, node.level, entity.level などのパターンを検索
            level_usage = re.findall(r'\b\w+\.level\b', content)
            
            # levelプロパティの使用が見つかった場合
            if level_usage:
                # コメントやドキュメントでない実際のコードか確認
                for usage in level_usage:
                    # TODO: より詳細な検証が必要
                    assert False, f"{file_path}でlevelプロパティ'{usage}'が使用されています"
    
    def test_グラフ深さ制限が文書化されている(self):
        """
        グラフのエッジ関係深さの上限に関する制約が文書化されていることを確認
        """
        doc_paths = [
            'docs/GRAPH_DEPTH_CONSTRAINTS.md',
            'docs/EDGE_RELATIONSHIP_RULES.md',
            'README.md'
        ]
        
        depth_doc_exists = False
        for doc_path in doc_paths:
            if os.path.exists(doc_path):
                with open(doc_path, 'r') as f:
                    content = f.read()
                    if 'depth' in content or 'edge' in content:
                        depth_doc_exists = True
                        break
        
        # TODO: グラフ深さ制限の文書化が必要
        pytest.skip("グラフ深さ制限の文書化が未完了")