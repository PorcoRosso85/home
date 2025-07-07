"""
グラフベース検証器のテスト
"""
import pytest
from .graph_depth_validator import GraphDepthValidator
from .circular_reference_detector import CircularReferenceDetector


class TestGraphDepthValidator:
    """グラフ深さ検証器のテスト"""
    
    def test_深さ制限内の場合は有効(self):
        """設定された深さ制限内の依存関係は有効"""
        validator = GraphDepthValidator(max_depth=3)
        
        # A -> B -> C -> D (深さ3)
        dependencies = [("A", "B"), ("B", "C"), ("C", "D")]
        result = validator.validate_graph_depth(dependencies)
        
        assert result["is_valid"] == True
        assert result["max_depth_found"] == 3
        assert len(result["violations"]) == 0
    
    def test_深さ制限を超える場合は無効(self):
        """設定された深さ制限を超える依存関係は無効"""
        validator = GraphDepthValidator(max_depth=3)
        
        # A -> B -> C -> D -> E (深さ4)
        dependencies = [("A", "B"), ("B", "C"), ("C", "D"), ("D", "E")]
        result = validator.validate_graph_depth(dependencies)
        
        assert result["is_valid"] == False
        assert result["max_depth_found"] == 4
        assert len(result["violations"]) > 0
        
        # 違反の詳細を確認
        violation = result["violations"][0]
        assert violation["depth"] == 4
        assert violation["max_allowed"] == 3
    
    def test_制限なしの場合は常に有効(self):
        """深さ制限がNoneの場合は常に有効"""
        validator = GraphDepthValidator(max_depth=None)
        
        # 非常に深い依存関係
        dependencies = [
            ("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"),
            ("E", "F"), ("F", "G"), ("G", "H"), ("H", "I")
        ]
        result = validator.validate_graph_depth(dependencies)
        
        assert result["is_valid"] == True
        assert result["max_depth_found"] == 8
        assert len(result["violations"]) == 0


class TestCircularReferenceDetector:
    """循環参照検出器のテスト"""
    
    def test_自己参照を検出(self):
        """ノードが自分自身を参照する場合を検出"""
        detector = CircularReferenceDetector()
        
        dependencies = [("A", "A")]
        result = detector.detect_cycles(dependencies)
        
        assert result["has_cycles"] == True
        assert "A" in result["self_references"]
        assert result["total_violations"] >= 1
    
    def test_単純な循環を検出(self):
        """A -> B -> C -> A の循環を検出"""
        detector = CircularReferenceDetector()
        
        dependencies = [("A", "B"), ("B", "C"), ("C", "A")]
        result = detector.detect_cycles(dependencies)
        
        assert result["has_cycles"] == True
        assert len(result["cycles"]) > 0
        
        # 循環パスにA, B, Cが含まれることを確認
        cycle = result["cycles"][0]
        assert all(node in cycle for node in ["A", "B", "C"])
    
    def test_循環がない場合(self):
        """循環がない正常な依存関係"""
        detector = CircularReferenceDetector()
        
        dependencies = [("A", "B"), ("B", "C"), ("C", "D")]
        result = detector.detect_cycles(dependencies)
        
        assert result["has_cycles"] == False
        assert len(result["cycles"]) == 0
        assert len(result["self_references"]) == 0
        assert result["total_violations"] == 0
    
    def test_複雑な循環を検出(self):
        """複数の循環が存在する場合"""
        detector = CircularReferenceDetector()
        
        dependencies = [
            # 循環1: A -> B -> A
            ("A", "B"), ("B", "A"),
            # 循環2: C -> D -> E -> C
            ("C", "D"), ("D", "E"), ("E", "C"),
            # 正常な依存
            ("F", "G"), ("G", "H")
        ]
        result = detector.detect_cycles(dependencies)
        
        assert result["has_cycles"] == True
        assert len(result["cycles"]) >= 2  # 少なくとも2つの循環