"""
階層概念への依存がないことを確認するテスト
"""
import os
import re
import pytest


class TestNoHierarchyAssumption:
    """システムが固定的な階層概念に依存していないことを確認"""
    
    def test_hierarchy_levelプロパティを使用しているコードを検出(self):
        """
        hierarchy_levelプロパティの使用箇所を検出
        （本来は使用すべきでない）
        """
        hierarchy_level_usage = []
        
        for root, dirs, files in os.walk('.'):
            if '.venv' in root or '__pycache__' in root or '.git' in root:
                continue
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        # hierarchy_levelの使用を検索
                        matches = re.findall(r'hierarchy_level["\']?\s*[:=]', content)
                        if matches:
                            hierarchy_level_usage.append(file_path)
                    except:
                        pass
        
        # 実際に使用箇所があることを確認（現状）
        assert len(hierarchy_level_usage) > 0, \
            "hierarchy_levelの使用が見つかりません（既に削除済み？）"
        
        # TODO: 将来的にはこのアサーションに変更
        # assert len(hierarchy_level_usage) == 0, \
        #     f"hierarchy_levelを使用しているファイル: {hierarchy_level_usage}"
        
        print(f"\nhierarchy_levelを使用しているファイル数: {len(hierarchy_level_usage)}")
        for f in hierarchy_level_usage[:5]:  # 最初の5件を表示
            print(f"  - {f}")
    
    def test_固定レベル0から4への依存を検出(self):
        """
        レベル0-4の固定値への依存を検出
        """
        fixed_level_usage = []
        
        # レベル値への直接的な依存を探すパターン
        patterns = [
            r'level\s*==\s*[0-4]',
            r'level\s*[<>]=?\s*[0-4]',
            r'hierarchy_level\s*==\s*[0-4]',
            r'hierarchy_level\s*[<>]=?\s*[0-4]',
            r'"vision".*0|0.*"vision"',
            r'"task".*4|4.*"task"'
        ]
        
        for root, dirs, files in os.walk('.'):
            if '.venv' in root or '__pycache__' in root or '.git' in root:
                continue
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        for pattern in patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                fixed_level_usage.append(file_path)
                                break
                    except:
                        pass
        
        # 実際に使用箇所があることを確認（現状）
        assert len(fixed_level_usage) > 0, \
            "固定レベルへの依存が見つかりません（既に削除済み？）"
        
        print(f"\n固定レベル(0-4)を使用しているファイル数: {len(fixed_level_usage)}")
        for f in fixed_level_usage[:5]:
            print(f"  - {f}")
    
    def test_階層違反という概念への依存を検出(self):
        """
        '階層違反'という概念を使用している箇所を検出
        """
        hierarchy_violation_usage = []
        
        patterns = [
            r'階層違反',
            r'hierarchy.?violation',
            r'level.?violation',
            r'レベル.*違反',
            r'違反.*レベル'
        ]
        
        for root, dirs, files in os.walk('.'):
            if '.venv' in root or '__pycache__' in root or '.git' in root:
                continue
            
            for file in files:
                if file.endswith(('.py', '.md')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        for pattern in patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                hierarchy_violation_usage.append(file_path)
                                break
                    except:
                        pass
        
        print(f"\n階層違反概念を使用しているファイル数: {len(hierarchy_violation_usage)}")
        for f in hierarchy_violation_usage[:5]:
            print(f"  - {f}")