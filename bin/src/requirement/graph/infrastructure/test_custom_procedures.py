"""
Tests for Custom Procedures
"""
from .custom_procedures import CustomProcedures


def test_find_similar_requirements_returns_list():
    """find_similar_requirements_類似要件リストを返す"""
    # Arrange
    # テスト用の接続クラスを定義
    class TestConnection:
        def __init__(self):
            self.requirements = {
                "req_001": {"id": "req_001", "title": "データベース移行", "description": "KuzuDBへの移行", "embedding": self._create_embedding("データベース移行 KuzuDBへの移行")},
                "req_002": {"id": "req_002", "title": "API設計", "description": "RESTful API実装", "embedding": self._create_embedding("API設計 RESTful API実装")}
            }
            
        def _create_embedding(self, text):
            embedding = [0.1] * 50
            for i, char in enumerate(text[:10]):
                embedding[i % 50] += ord(char) / 1000.0
            norm = sum(x*x for x in embedding) ** 0.5
            if norm > 0:
                embedding = [x / norm for x in embedding]
            return embedding
            
        def execute(self, query, parameters=None):
            if "MATCH (r:RequirementEntity {id: $req_id})" in query:
                req_id = parameters.get("req_id")
                if req_id in self.requirements:
                    return TestResult([[self.requirements[req_id]]])
            elif "MATCH (r:RequirementEntity)" in query:
                return TestResult([[req] for req in self.requirements.values()])
            return TestResult([])
    
    class TestResult:
        def __init__(self, data):
            self.data = data
            self._index = 0
        
        def has_next(self):
            return self._index < len(self.data)
        
        def get_next(self):
            if self.has_next():
                result = self.data[self._index]
                self._index += 1
                return result
            return None
    
    conn = TestConnection()
    procedures = CustomProcedures(conn)
    
    # Act
    results = procedures.find_similar_requirements(
        "req_001",
        "グラフデータベースの導入"
    )
    
    # Assert
    assert isinstance(results, list), f"Expected list but got {type(results)}"
    if results:
        assert "id" in results[0]
        assert "title" in results[0]
        assert "similarity" in results[0]


def test_check_constraint_violations_detects_issues():
    """check_constraint_violations_制約違反を検出"""
    # Arrange
    # テスト用接続クラスを定義
    class TestConnection:
        def __init__(self):
            self.requirements = {
                "req_001": {"id": "req_001", "title": "要件A", "description": "説明A"},
                "req_002": {"id": "req_002", "title": "要件B", "description": "説明B"},
                "req_003": {"id": "req_003", "title": "要件C", "description": "説明C"}
            }
            self.dependencies = [("req_001", "req_002"), ("req_002", "req_003"), ("req_003", "req_001")]
            
        def execute(self, query, parameters=None):
            # 循環依存チェックのクエリ
            if "path = (start:RequirementEntity {id: $req_id})-[:DEPENDS_ON*]->(end:RequirementEntity)" in query:
                req_id = parameters.get("req_id")
                if req_id == "req_001":
                    # 循環を検出
                    return TestResult([[{"path": "req_001->req_002->req_003->req_001"}]])
            # 深度チェック
            elif "length(path) as depth" in query:
                return TestResult([[1]])  # 深度1
            return TestResult([])
    
    class TestResult:
        def __init__(self, data):
            self.data = data
            self._index = 0
        
        def has_next(self):
            return self._index < len(self.data)
        
        def get_next(self):
            if self.has_next():
                result = self.data[self._index]
                self._index += 1
                return result
            return None
    
    conn = TestConnection()
    procedures = CustomProcedures(conn)
    
    # Act
    result = procedures.check_constraint_violations("req_001")
    
    # Assert
    assert isinstance(result, dict), f"Expected dict but got {type(result)}"
    assert "violations" in result, f"Expected 'violations' in {result}"
    assert len(result["violations"]) > 0, f"Expected violations but got {result['violations']}"


def test_calculate_progress_with_children_returns_completion_rate():
    """calculate_progress_子要件含む_完了率を返す"""
    # Arrange
    class TestConnection:
        def __init__(self):
            self.requirements = {
                "req_001": {"id": "req_001", "title": "親要件", "description": "説明", "status": "approved"},
                "req_002": {"id": "req_002", "title": "子要件1", "description": "説明", "status": "completed"},
                "req_003": {"id": "req_003", "title": "子要件2", "description": "説明", "status": "proposed"}
            }
            self.parent_child = [("req_001", "req_002"), ("req_001", "req_003")]
            
        def execute(self, query, parameters=None):
            if "MATCH (parent:RequirementEntity {id: $parent_id})-[:PARENT_OF]->(child:RequirementEntity)" in query:
                parent_id = parameters.get("parent_id")
                if parent_id == "req_001":
                    # 子要件のステータスを返す
                    if "RETURN child.status" in query:
                        return TestResult([["completed"], ["proposed"]])
                    else:
                        return TestResult([[self.requirements["req_002"]], [self.requirements["req_003"]]])
            elif "MATCH (r:RequirementEntity {id: $req_id}) RETURN r.status" in query:
                req_id = parameters.get("req_id")
                if req_id in self.requirements:
                    return TestResult([[self.requirements[req_id]["status"]]])
            return TestResult([])
    
    class TestResult:
        def __init__(self, data):
            self.data = data
            self._index = 0
        
        def has_next(self):
            return self._index < len(self.data)
        
        def get_next(self):
            if self.has_next():
                result = self.data[self._index]
                self._index += 1
                return result
            return None
    
    conn = TestConnection()
    procedures = CustomProcedures(conn)
    
    # Act
    results = procedures.calculate_progress("req_001", include_children=True)
    
    # Assert
    progress, details = results[0]
    assert 0.0 <= progress <= 1.0
    assert progress == 0.5  # 子要件の1/2が完了
    assert "completed_count" in details
    assert "total_count" in details


def test_validate_constraints_add_dependency_detects_circular():
    """validate_constraints_依存追加_循環を検出"""
    # Arrange
    class TestConnection:
        def __init__(self):
            self.requirements = {
                "req_001": {"id": "req_001", "title": "要件A", "description": "説明A"},
                "req_002": {"id": "req_002", "title": "要件B", "description": "説明B"}
            }
            self.dependencies = [("req_002", "req_001")]  # req_002 -> req_001
            
        def execute(self, query, parameters=None):
            # 循環依存チェックのクエリ
            if "path = (start:RequirementEntity {id: $target_id})-[:DEPENDS_ON*]->(end:RequirementEntity {id: $req_id})" in query:
                target_id = parameters.get("target_id")
                req_id = parameters.get("req_id")
                # req_002 -> req_001の経路が存在するかチェック
                if target_id == "req_002" and req_id == "req_001":
                    return TestResult([[True]])  # 経路あり = 循環になる
            return TestResult([])
    
    class TestResult:
        def __init__(self, data):
            self.data = data
            self._index = 0
        
        def has_next(self):
            return self._index < len(self.data)
        
        def get_next(self):
            if self.has_next():
                result = self.data[self._index]
                self._index += 1
                return result
            return None
    
    conn = TestConnection()
    procedures = CustomProcedures(conn)
    
    # Act - req_001 -> req_002を追加しようとする（循環になる）
    results = procedures.validate_constraints(
        "req_001",
        "add_dependency",
        "req_002"
    )
    
    # Assert
    is_valid, violations = results[0]
    assert is_valid is False
    assert "circular_dependency" in violations


def test_analyze_impact_modify_returns_affected_requirements():
    """analyze_impact_変更時_影響要件を返す"""
    # Arrange
    class TestConnection:
        def __init__(self):
            self.requirements = {
                "req_001": {"id": "req_001", "title": "基盤要件", "description": "説明"},
                "req_002": {"id": "req_002", "title": "依存要件1", "description": "説明"},
                "req_003": {"id": "req_003", "title": "依存要件2", "description": "説明"}
            }
            self.dependencies = [("req_002", "req_001"), ("req_003", "req_001")]
            
        def execute(self, query, parameters=None):
            # 依存している要件を取得するクエリ
            if "MATCH (r:RequirementEntity)-[:DEPENDS_ON]->(target:RequirementEntity {id: $req_id})" in query:
                req_id = parameters.get("req_id")
                if req_id == "req_001":
                    # req_001に依存している要件を返す
                    return TestResult([[self.requirements["req_002"]], [self.requirements["req_003"]]])
            return TestResult([])
    
    class TestResult:
        def __init__(self, data):
            self.data = data
            self._index = 0
        
        def has_next(self):
            return self._index < len(self.data)
        
        def get_next(self):
            if self.has_next():
                result = self.data[self._index]
                self._index += 1
                return result
            return None
    
    conn = TestConnection()
    procedures = CustomProcedures(conn)
    
    # Act
    result = procedures.analyze_impact("req_001", "modify")
    
    # Assert
    assert isinstance(result, dict), f"Expected dict but got {type(result)}"
    assert "affected_requirements" in result
    assert "affected_count" in result
    assert result["affected_count"] == 2, f"Expected 2 affected requirements but got {result['affected_count']}"
    affected = result["affected_requirements"]
    affected_ids = [r["id"] for r in affected]
    assert "req_002" in affected_ids, f"Expected req_002 in {affected_ids}"
    assert "req_003" in affected_ids, f"Expected req_003 in {affected_ids}"


# 各テスト関数内でテスト用クラスを定義して使用