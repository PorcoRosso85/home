"""
移行後の新スキーマで重要機能が実現できることを検証するテスト
明確な要件が与えられた場合の5つの優先機能をテスト
"""
import pytest
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# 最適化機能をインポート
from .application.optimization_features import (
    optimize_implementation_order_with_layers,
    find_critical_path,
    calculate_foundation_priority,
    suggest_requirement_split,
    check_technical_feasibility,
    extract_common_components,
    estimate_effort
)


class TestImplementationOrderOptimization:
    """実装順序の最適化機能のテスト"""
    
    def test_technical_layer_ordering_DB優先_正しい順序(self):
        """技術レイヤー_DB→API→UI_実装順序を最適化"""
        # Arrange - 新スキーマのデータ
        requirements = [
            {"id": "req_ui_001", "title": "ユーザー画面"},
            {"id": "req_api_001", "title": "REST API"},
            {"id": "req_db_001", "title": "データベース設計"}
        ]
        
        code_entities = [
            {"persistent_id": "ui_component", "type": "ui", "complexity": 10},
            {"persistent_id": "api_endpoint", "type": "api", "complexity": 15},
            {"persistent_id": "db_schema", "type": "database", "complexity": 20}
        ]
        
        implementation_relations = [
            ("req_ui_001", "ui_component", "direct"),
            ("req_api_001", "api_endpoint", "direct"),
            ("req_db_001", "db_schema", "direct")
        ]
        
        dependencies = [
            ("req_ui_001", "req_api_001", "technical"),
            ("req_api_001", "req_db_001", "technical")
        ]
        
        # Act
        optimized_order = optimize_implementation_order_with_layers(
            requirements, code_entities, implementation_relations, dependencies
        )
        
        # Assert
        assert optimized_order == ["req_db_001", "req_api_001", "req_ui_001"]
        
    def test_critical_path_detection_最長パス_優先実装(self):
        """クリティカルパス_最長依存チェーン_優先的に実装"""
        # Arrange - ダイヤモンド依存 + 追加パス
        dependencies_graph = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["D"],
            "D": ["E"],
            "E": [],
            "F": ["G"],
            "G": []
        }
        
        # Act
        critical_path = find_critical_path(dependencies_graph)
        
        # Assert
        # A→B→D→E または A→C→D→E が最長パス（長さ4）
        assert len(critical_path) == 4
        assert critical_path[0] == "A"
        assert critical_path[-1] == "E"
        
    def test_shared_foundation_priority_共通基盤_先行実装(self):
        """共通基盤_複数要件が依存_優先度を上げる"""
        # Arrange
        requirements = [
            {"id": "auth_req", "title": "認証機能"},
            {"id": "user_req", "title": "ユーザー管理"},
            {"id": "logging_req", "title": "ログ基盤"},
            {"id": "payment_req", "title": "決済機能"}
        ]
        
        # 認証とユーザー管理の両方がログ基盤に依存
        dependencies = [
            ("auth_req", "logging_req"),
            ("user_req", "logging_req"),
            ("payment_req", "auth_req")
        ]
        
        # Act
        priority_scores = calculate_foundation_priority(requirements, dependencies)
        
        # Assert
        assert priority_scores["logging_req"] > priority_scores["auth_req"]
        assert priority_scores["logging_req"] > priority_scores["user_req"]
        assert priority_scores["auth_req"] > priority_scores["payment_req"]


class TestGranularityOptimization:
    """分解粒度の適正化機能のテスト"""
    
    def test_complexity_based_granularity_複雑度_分割提案(self):
        """高複雑度_閾値超過_分割を提案"""
        # Arrange - 新スキーマでの複雑度評価
        requirement = {"id": "complex_req", "title": "複雑な機能"}
        
        code_implementations = [
            {"persistent_id": "func1", "complexity": 50, "lines": 500},
            {"persistent_id": "func2", "complexity": 60, "lines": 600},
            {"persistent_id": "func3", "complexity": 40, "lines": 400}
        ]
        
        location_hierarchy = {
            "depth": 2,  # L0/vision/L1/impl/complex_req
            "siblings": 0
        }
        
        # Act
        granularity_assessment = assess_requirement_granularity(
            requirement, code_implementations, location_hierarchy
        )
        
        # Assert
        assert granularity_assessment["is_too_large"] == True
        assert granularity_assessment["total_complexity"] == 150
        assert granularity_assessment["recommendation"] == "split"
        assert len(granularity_assessment["split_suggestions"]) >= 3
        
    def test_hierarchy_depth_check_深い階層_警告(self):
        """階層深度_5階層以上_分解見直しを提案"""
        # Arrange
        location_uri = "req://L0/vision/L1/arch/L2/api/L3/auth/L4/jwt/L5/validation/req_001"
        
        # Act
        depth_analysis = analyze_hierarchy_depth(location_uri)
        
        # Assert
        assert depth_analysis["depth"] == 6  # L0からL5まで
        assert depth_analysis["warning"] == "too_deep"
        assert "flatten" in depth_analysis["suggestions"]
        
    def test_implementation_size_estimation_実装サイズ_適切な粒度(self):
        """実装サイズ_1-2週間_適切な粒度と判定"""
        # Arrange
        code_entity = {
            "persistent_id": "auth_service",
            "complexity": 25,  # 中程度の複雑度
            "start_position": 100,
            "end_position": 600  # 500行
        }
        
        # Act
        size_estimate = estimate_implementation_size(code_entity)
        
        # Assert
        assert size_estimate["estimated_days"] >= 5
        assert size_estimate["estimated_days"] <= 10
        assert size_estimate["size_category"] == "medium"
        assert size_estimate["is_appropriate_size"] == True


class TestTechnicalFeasibilityCheck:
    """技術的実現可能性チェック機能のテスト"""
    
    def test_external_dependency_check_外部依存_ブロッカー検出(self):
        """外部ライブラリ_未準備_実装ブロックを検出"""
        # Arrange - ReferenceEntityを使った依存チェック
        requirement = {"id": "oauth_req", "title": "OAuth認証"}
        
        code_entity = {"persistent_id": "oauth_handler", "name": "OAuthHandler"}
        
        external_references = [
            {
                "id": "ref_oauth_lib",
                "type": "library",
                "source_type": "external",
                "status": "not_available",  # 拡張属性
                "description": "OAuth2.0 client library v3.0"
            }
        ]
        
        refers_to_relations = [("oauth_handler", "ref_oauth_lib")]
        
        # Act
        feasibility = check_technical_feasibility(
            requirement, code_entity, external_references, refers_to_relations
        )
        
        # Assert
        assert feasibility["is_feasible"] == False
        assert feasibility["blockers"][0]["type"] == "external_dependency"
        assert feasibility["blockers"][0]["ref_id"] == "ref_oauth_lib"
        assert "OAuth2.0 client library" in feasibility["blockers"][0]["description"]
        
    def test_api_version_compatibility_API互換性_警告(self):
        """API仕様_バージョン不一致_互換性警告"""
        # Arrange
        references = [
            {
                "id": "ref_payment_api",
                "type": "api",
                "source_type": "external",
                "description": "Payment Gateway API v2.0",
                "required_version": "2.0",
                "available_version": "1.5"
            }
        ]
        
        # Act
        compatibility = check_api_compatibility(references)
        
        # Assert
        assert compatibility["has_issues"] == True
        assert compatibility["issues"][0]["type"] == "version_mismatch"
        assert compatibility["issues"][0]["severity"] == "warning"
        
    def test_database_constraint_check_DB制約_実装順序に影響(self):
        """データベース制約_外部キー_実装順序を制限"""
        # Arrange
        code_entities = [
            {"persistent_id": "user_table", "type": "database", "name": "users"},
            {"persistent_id": "order_table", "type": "database", "name": "orders"},
            {"persistent_id": "product_table", "type": "database", "name": "products"}
        ]
        
        # ordersテーブルはusersとproductsに依存
        code_dependencies = [
            ("order_table", "user_table", "foreign_key"),
            ("order_table", "product_table", "foreign_key")
        ]
        
        # Act
        constraints = analyze_database_constraints(code_entities, code_dependencies)
        
        # Assert
        assert constraints["creation_order"] == ["user_table", "product_table", "order_table"]
        assert constraints["has_circular"] == False


class TestSharedComponentExtraction:
    """共通コンポーネントの抽出機能のテスト"""
    
    def test_shared_code_detection_複数要件_共通実装を検出(self):
        """共通コード_複数要件が参照_再利用候補として抽出"""
        # Arrange - IS_IMPLEMENTED_BY関係から共通コードを検出
        implementation_relations = [
            ("req_001", "validation_utils", "direct"),
            ("req_002", "validation_utils", "direct"),
            ("req_003", "validation_utils", "direct"),
            ("req_001", "auth_handler", "direct"),
            ("req_002", "user_service", "direct")
        ]
        
        # Act
        shared_components = extract_shared_components(implementation_relations)
        
        # Assert
        assert "validation_utils" in shared_components
        assert len(shared_components["validation_utils"]["used_by"]) == 3
        assert shared_components["validation_utils"]["reuse_score"] > 0.8
        assert "auth_handler" not in shared_components  # 1要件のみ
        
    def test_shared_reference_pattern_共通参照_ライブラリ統一(self):
        """外部参照_複数が同一ライブラリ参照_統一管理を提案"""
        # Arrange - 複数のコードが同じ外部ライブラリを参照
        refers_to_relations = [
            ("func_a", "ref_json_lib", "library"),
            ("func_b", "ref_json_lib", "library"),
            ("func_c", "ref_json_lib", "library"),
            ("func_d", "ref_xml_lib", "library")
        ]
        
        reference_entities = [
            {"id": "ref_json_lib", "description": "JSON parsing library"},
            {"id": "ref_xml_lib", "description": "XML parsing library"}
        ]
        
        # Act
        shared_refs = analyze_shared_references(refers_to_relations, reference_entities)
        
        # Assert
        assert shared_refs["ref_json_lib"]["usage_count"] == 3
        assert shared_refs["ref_json_lib"]["recommendation"] == "create_wrapper"
        assert shared_refs["ref_xml_lib"]["usage_count"] == 1
        
    def test_data_model_commonality_データモデル_共通フィールド抽出(self):
        """データ構造_類似フィールド_共通モデルを提案"""
        # Arrange - コードエンティティの実装詳細から推定
        code_entities = [
            {
                "persistent_id": "user_model",
                "name": "UserModel",
                "type": "class",
                "signature": "class UserModel(id, name, email, created_at)"
            },
            {
                "persistent_id": "customer_model",
                "name": "CustomerModel",
                "type": "class",
                "signature": "class CustomerModel(id, name, email, phone, created_at)"
            },
            {
                "persistent_id": "admin_model",
                "name": "AdminModel",
                "type": "class",
                "signature": "class AdminModel(id, name, email, role, created_at)"
            }
        ]
        
        # Act
        common_fields = extract_common_data_fields(code_entities)
        
        # Assert
        assert set(common_fields["common"]) == {"id", "name", "email", "created_at"}
        assert common_fields["suggestion"]["name"] == "BaseUserModel"
        assert common_fields["suggestion"]["inheritance_candidates"] == [
            "user_model", "customer_model", "admin_model"
        ]


class TestEffortEstimation:
    """実装工数の自動見積もり機能のテスト"""
    
    def test_complexity_based_estimation_複雑度_工数を推定(self):
        """コード複雑度_集計_ストーリーポイントを算出"""
        # Arrange - 要件に関連するコードエンティティ
        requirement = {"id": "payment_req", "title": "決済機能"}
        
        related_code_entities = [
            {"persistent_id": "payment_api", "complexity": 30, "lines": 300},
            {"persistent_id": "payment_validator", "complexity": 15, "lines": 150},
            {"persistent_id": "payment_db", "complexity": 20, "lines": 100}
        ]
        
        # Act
        effort_estimate = estimate_requirement_effort(requirement, related_code_entities)
        
        # Assert
        assert effort_estimate["total_complexity"] == 65
        assert effort_estimate["total_lines"] == 550
        assert effort_estimate["story_points"] >= 5  # 中規模タスク
        assert effort_estimate["story_points"] <= 13
        assert effort_estimate["estimated_days"] >= 3
        assert effort_estimate["estimated_days"] <= 10
        
    def test_historical_velocity_過去実績_精度向上(self):
        """過去の類似要件_完了時間_ベロシティベースで補正"""
        # Arrange - VersionStateとRequirementSnapshotから履歴データ
        historical_data = [
            {
                "requirement_id": "past_auth_001",
                "complexity": 50,
                "actual_days": 8,
                "completion_date": "2024-01-15"
            },
            {
                "requirement_id": "past_auth_002",
                "complexity": 45,
                "actual_days": 7,
                "completion_date": "2024-02-01"
            }
        ]
        
        current_requirement = {
            "id": "new_auth_001",
            "estimated_complexity": 48
        }
        
        # Act
        adjusted_estimate = adjust_estimate_with_velocity(
            current_requirement, historical_data
        )
        
        # Assert
        assert adjusted_estimate["base_estimate"] > 0
        assert adjusted_estimate["velocity_factor"] > 0  # 複雑度/実日数
        assert adjusted_estimate["adjusted_days"] >= 7
        assert adjusted_estimate["adjusted_days"] <= 8
        assert adjusted_estimate["confidence"] > 0.7  # 類似データあり
        
    def test_team_capacity_consideration_チーム規模_並列可能性(self):
        """チーム構成_並列実装可能_工数短縮を考慮"""
        # Arrange - 独立した実装単位
        implementation_units = [
            {"id": "ui_impl", "effort": 5, "dependencies": []},
            {"id": "api_impl", "effort": 8, "dependencies": []},
            {"id": "db_impl", "effort": 3, "dependencies": []},
            {"id": "integration", "effort": 4, "dependencies": ["ui_impl", "api_impl", "db_impl"]}
        ]
        
        team_size = 3
        
        # Act
        schedule = calculate_parallel_schedule(implementation_units, team_size)
        
        # Assert
        # UI, API, DBは並列実装可能
        assert schedule["total_duration"] == 12  # max(5,8,3) + 4
        assert schedule["critical_path"] == ["api_impl", "integration"]
        assert len(schedule["parallel_tracks"]) == 3


# ヘルパー関数の実装

def optimize_implementation_order_with_layers(
    requirements: List[Dict],
    code_entities: List[Dict],
    implementation_relations: List[Tuple],
    dependencies: List[Tuple]
) -> List[str]:
    """技術レイヤーと依存関係を考慮した実装順序の最適化"""
    # 要件とコードエンティティのマッピング
    req_to_code = {}
    for req_id, code_id, _ in implementation_relations:
        req_to_code[req_id] = code_id
    
    # コードエンティティのタイプマッピング
    code_types = {c["persistent_id"]: c["type"] for c in code_entities}
    
    # レイヤー優先度
    layer_priority = {"database": 1, "api": 2, "ui": 3, "other": 4}
    
    # 依存グラフの構築
    dep_graph = {}
    for from_req, to_req, _ in dependencies:
        if from_req not in dep_graph:
            dep_graph[from_req] = []
        dep_graph[to_req] = []  # 依存先も初期化
    
    for from_req, to_req, _ in dependencies:
        dep_graph[from_req].append(to_req)
    
    # トポロジカルソート with レイヤー考慮
    visited = set()
    result = []
    
    def dfs(req_id):
        if req_id in visited:
            return
        visited.add(req_id)
        
        # 依存先を先に処理
        for dep in dep_graph.get(req_id, []):
            dfs(dep)
        
        result.append(req_id)
    
    # レイヤー順でソートしてから処理
    sorted_reqs = sorted(requirements, key=lambda r: 
        layer_priority.get(
            code_types.get(req_to_code.get(r["id"], ""), "other"),
            4
        )
    )
    
    for req in sorted_reqs:
        if req["id"] not in visited:
            dfs(req["id"])
    
    return result


def find_critical_path(dependencies_graph: Dict[str, List[str]]) -> List[str]:
    """最長パス（クリティカルパス）を見つける"""
    # 各ノードからの最長パスを計算
    longest_paths = {}
    
    def calculate_longest_path(node):
        if node in longest_paths:
            return longest_paths[node]
        
        if not dependencies_graph.get(node):
            longest_paths[node] = [node]
            return [node]
        
        max_path = []
        for next_node in dependencies_graph[node]:
            path = calculate_longest_path(next_node)
            if len(path) > len(max_path):
                max_path = path
        
        longest_paths[node] = [node] + max_path
        return longest_paths[node]
    
    # すべてのノードから計算
    all_paths = []
    for node in dependencies_graph:
        path = calculate_longest_path(node)
        all_paths.append(path)
    
    # 最長のパスを返す
    return max(all_paths, key=len)


def calculate_foundation_priority(requirements: List[Dict], dependencies: List[Tuple]) -> Dict[str, float]:
    """共通基盤の優先度を計算"""
    # 各要件が依存されている回数をカウント
    dependency_count = {}
    for req in requirements:
        dependency_count[req["id"]] = 0
    
    for from_req, to_req in dependencies:
        dependency_count[to_req] = dependency_count.get(to_req, 0) + 1
    
    # 推移的な依存も考慮
    transitive_impact = {}
    
    def calculate_impact(req_id, visited=None):
        if visited is None:
            visited = set()
        
        if req_id in visited:
            return 0
        
        visited.add(req_id)
        impact = 1  # 自身
        
        # この要件に依存しているものを数える
        for from_req, to_req in dependencies:
            if to_req == req_id:
                impact += calculate_impact(from_req, visited.copy())
        
        return impact
    
    for req in requirements:
        transitive_impact[req["id"]] = calculate_impact(req["id"])
    
    # 優先度スコア = 直接依存数 + 推移的影響の重み付け
    priority_scores = {}
    for req_id in dependency_count:
        priority_scores[req_id] = (
            dependency_count[req_id] * 2 +  # 直接依存は重要
            transitive_impact.get(req_id, 0) * 0.5
        )
    
    return priority_scores


def assess_requirement_granularity(
    requirement: Dict,
    code_implementations: List[Dict],
    location_hierarchy: Dict
) -> Dict:
    """要件の粒度を評価"""
    total_complexity = sum(c["complexity"] for c in code_implementations)
    total_lines = sum(c.get("lines", 0) for c in code_implementations)
    
    # 複雑度の閾値（1-2週間で実装可能な範囲）
    COMPLEXITY_THRESHOLD = 100
    LINES_THRESHOLD = 1000
    
    is_too_large = (
        total_complexity > COMPLEXITY_THRESHOLD or 
        total_lines > LINES_THRESHOLD or
        location_hierarchy["depth"] > 4
    )
    
    # 分割提案
    split_suggestions = []
    if is_too_large:
        # 複雑度の高いものから分割
        sorted_impls = sorted(code_implementations, key=lambda x: x["complexity"], reverse=True)
        for impl in sorted_impls[:3]:  # 上位3つ
            split_suggestions.append({
                "target": impl["persistent_id"],
                "reason": f"High complexity: {impl['complexity']}"
            })
    
    return {
        "is_too_large": is_too_large,
        "total_complexity": total_complexity,
        "total_lines": total_lines,
        "recommendation": "split" if is_too_large else "appropriate",
        "split_suggestions": split_suggestions
    }


def analyze_hierarchy_depth(location_uri: str) -> Dict:
    """階層の深さを分析"""
    parts = location_uri.split("/")
    # req:// の後のパーツをカウント
    hierarchy_parts = [p for p in parts[2:] if p and not p.startswith("req_")]
    depth = len(hierarchy_parts)
    
    suggestions = []
    if depth > 5:
        suggestions.append("flatten")
        suggestions.append("consolidate_intermediate_levels")
    
    return {
        "depth": depth,
        "warning": "too_deep" if depth > 5 else "ok",
        "suggestions": suggestions
    }


def estimate_implementation_size(code_entity: Dict) -> Dict:
    """実装サイズを推定"""
    complexity = code_entity["complexity"]
    lines = code_entity["end_position"] - code_entity["start_position"]
    
    # 経験則ベースの推定
    # 複雑度10 ≈ 1日、100行 ≈ 1日
    estimated_days = (complexity / 10) + (lines / 100)
    
    if estimated_days < 3:
        size_category = "small"
    elif estimated_days <= 10:
        size_category = "medium"
    else:
        size_category = "large"
    
    return {
        "estimated_days": estimated_days,
        "size_category": size_category,
        "is_appropriate_size": 3 <= estimated_days <= 10
    }


def check_technical_feasibility(
    requirement: Dict,
    code_entity: Dict,
    external_references: List[Dict],
    refers_to_relations: List[Tuple]
) -> Dict:
    """技術的実現可能性をチェック"""
    blockers = []
    
    # コードが参照する外部依存をチェック
    for code_id, ref_id in refers_to_relations:
        if code_id == code_entity["persistent_id"]:
            # 対応する参照を探す
            for ref in external_references:
                if ref["id"] == ref_id:
                    if ref.get("status") == "not_available":
                        blockers.append({
                            "type": "external_dependency",
                            "ref_id": ref_id,
                            "description": ref["description"],
                            "severity": "blocker"
                        })
    
    return {
        "is_feasible": len(blockers) == 0,
        "blockers": blockers
    }


def check_api_compatibility(references: List[Dict]) -> Dict:
    """API互換性をチェック"""
    issues = []
    
    for ref in references:
        if ref["type"] == "api":
            required = ref.get("required_version")
            available = ref.get("available_version")
            
            if required and available and required != available:
                # バージョン比較（簡易版）
                req_major = int(required.split(".")[0])
                avail_major = int(available.split(".")[0])
                
                if req_major > avail_major:
                    severity = "error"
                else:
                    severity = "warning"
                
                issues.append({
                    "type": "version_mismatch",
                    "api": ref["description"],
                    "required": required,
                    "available": available,
                    "severity": severity
                })
    
    return {
        "has_issues": len(issues) > 0,
        "issues": issues
    }


def analyze_database_constraints(
    code_entities: List[Dict],
    code_dependencies: List[Tuple]
) -> Dict:
    """データベース制約を分析"""
    # DBテーブルのみ抽出
    db_tables = [e for e in code_entities if e["type"] == "database"]
    table_ids = {t["persistent_id"] for t in db_tables}
    
    # 依存グラフ構築
    dep_graph = {}
    for table in db_tables:
        dep_graph[table["persistent_id"]] = []
    
    for from_id, to_id, dep_type in code_dependencies:
        if from_id in table_ids and to_id in table_ids:
            dep_graph[from_id].append(to_id)
    
    # トポロジカルソート
    visited = set()
    temp_mark = set()
    order = []
    has_circular = False
    
    def visit(node):
        nonlocal has_circular
        if node in temp_mark:
            has_circular = True
            return
        if node in visited:
            return
        
        temp_mark.add(node)
        for neighbor in dep_graph.get(node, []):
            visit(neighbor)
        temp_mark.remove(node)
        visited.add(node)
        order.append(node)
    
    for node in dep_graph:
        if node not in visited:
            visit(node)
    
    order.reverse()
    
    return {
        "creation_order": order,
        "has_circular": has_circular
    }


def extract_shared_components(implementation_relations: List[Tuple]) -> Dict:
    """共通コンポーネントを抽出"""
    # コードエンティティごとの使用回数をカウント
    code_usage = {}
    
    for req_id, code_id, _ in implementation_relations:
        if code_id not in code_usage:
            code_usage[code_id] = {"used_by": [], "count": 0}
        code_usage[code_id]["used_by"].append(req_id)
        code_usage[code_id]["count"] += 1
    
    # 複数回使用されているものを抽出
    shared_components = {}
    for code_id, usage in code_usage.items():
        if usage["count"] > 1:
            shared_components[code_id] = {
                "used_by": usage["used_by"],
                "reuse_score": min(1.0, usage["count"] / 3.0)  # 3回以上で最大スコア
            }
    
    return shared_components


def analyze_shared_references(
    refers_to_relations: List[Tuple],
    reference_entities: List[Dict]
) -> Dict:
    """共有される外部参照を分析"""
    ref_usage = {}
    
    for code_id, ref_id, _ in refers_to_relations:
        if ref_id not in ref_usage:
            ref_usage[ref_id] = {"usage_count": 0, "used_by": []}
        ref_usage[ref_id]["usage_count"] += 1
        ref_usage[ref_id]["used_by"].append(code_id)
    
    # 参照エンティティの情報を追加
    for ref in reference_entities:
        if ref["id"] in ref_usage:
            ref_usage[ref["id"]]["description"] = ref["description"]
            # 3回以上使用されていたらラッパー作成を推奨
            if ref_usage[ref["id"]]["usage_count"] >= 3:
                ref_usage[ref["id"]]["recommendation"] = "create_wrapper"
            else:
                ref_usage[ref["id"]]["recommendation"] = "direct_use"
    
    return ref_usage


def extract_common_data_fields(code_entities: List[Dict]) -> Dict:
    """共通データフィールドを抽出"""
    import re
    
    # クラスのみ対象
    classes = [e for e in code_entities if e["type"] == "class"]
    
    # シグネチャからフィールドを抽出
    class_fields = {}
    for cls in classes:
        signature = cls.get("signature", "")
        # class Name(field1, field2, ...) パターン
        match = re.search(r'class\s+\w+\((.*?)\)', signature)
        if match:
            fields = [f.strip() for f in match.group(1).split(",")]
            class_fields[cls["persistent_id"]] = fields
    
    if not class_fields:
        return {"common": [], "suggestion": {}}
    
    # 共通フィールドを見つける
    all_fields = list(class_fields.values())
    common = set(all_fields[0])
    for fields in all_fields[1:]:
        common &= set(fields)
    
    # 基底クラスの提案
    suggestion = {}
    if len(common) >= 3:  # 3つ以上の共通フィールドがあれば
        suggestion = {
            "name": "BaseUserModel",
            "fields": list(common),
            "inheritance_candidates": list(class_fields.keys())
        }
    
    return {
        "common": list(common),
        "suggestion": suggestion
    }


def estimate_requirement_effort(
    requirement: Dict,
    related_code_entities: List[Dict]
) -> Dict:
    """要件の工数を推定"""
    total_complexity = sum(e["complexity"] for e in related_code_entities)
    total_lines = sum(e.get("lines", 0) for e in related_code_entities)
    
    # 複雑度ベースの推定
    # 複雑度10 ≈ 1日、100行 ≈ 0.5日
    complexity_days = total_complexity / 10
    lines_days = total_lines / 200
    
    estimated_days = max(complexity_days, lines_days)
    
    # ストーリーポイント（フィボナッチ数列）
    if estimated_days <= 2:
        story_points = 3
    elif estimated_days <= 4:
        story_points = 5
    elif estimated_days <= 7:
        story_points = 8
    elif estimated_days <= 10:
        story_points = 13
    else:
        story_points = 21
    
    return {
        "total_complexity": total_complexity,
        "total_lines": total_lines,
        "story_points": story_points,
        "estimated_days": estimated_days
    }


def adjust_estimate_with_velocity(
    current_requirement: Dict,
    historical_data: List[Dict]
) -> Dict:
    """過去の実績でベロシティ補正"""
    if not historical_data:
        return {
            "base_estimate": current_requirement["estimated_complexity"] / 10,
            "velocity_factor": 1.0,
            "adjusted_days": current_requirement["estimated_complexity"] / 10,
            "confidence": 0.3
        }
    
    # ベロシティ計算（複雑度/実日数）
    velocities = []
    for hist in historical_data:
        velocity = hist["complexity"] / hist["actual_days"]
        velocities.append(velocity)
    
    avg_velocity = sum(velocities) / len(velocities)
    
    # 現在の要件に適用
    base_estimate = current_requirement["estimated_complexity"] / 10
    adjusted_days = current_requirement["estimated_complexity"] / avg_velocity
    
    # 信頼度（データ数と類似度に基づく）
    confidence = min(0.9, 0.5 + len(historical_data) * 0.1)
    
    return {
        "base_estimate": base_estimate,
        "velocity_factor": avg_velocity,
        "adjusted_days": adjusted_days,
        "confidence": confidence
    }


def calculate_parallel_schedule(
    implementation_units: List[Dict],
    team_size: int
) -> Dict:
    """並列実装スケジュールを計算"""
    # 依存関係を考慮したスケジューリング
    completed = set()
    in_progress = {}
    schedule = []
    time = 0
    
    # 依存関係グラフ構築
    dep_graph = {}
    for unit in implementation_units:
        dep_graph[unit["id"]] = unit["dependencies"]
    
    # 利用可能なリソース
    available_resources = team_size
    
    while len(completed) < len(implementation_units):
        # 開始可能なタスクを探す
        ready_tasks = []
        for unit in implementation_units:
            if unit["id"] not in completed and unit["id"] not in in_progress:
                # 依存関係がすべて完了しているか
                if all(dep in completed for dep in unit["dependencies"]):
                    ready_tasks.append(unit)
        
        # リソースに応じてタスクを割り当て
        for task in ready_tasks[:available_resources]:
            in_progress[task["id"]] = {
                "start": time,
                "end": time + task["effort"],
                "effort": task["effort"]
            }
            available_resources -= 1
        
        # 時間を進める（最も早く終わるタスクまで）
        if in_progress:
            next_completion = min(info["end"] for info in in_progress.values())
            time = next_completion
            
            # 完了したタスクを処理
            completed_now = []
            for task_id, info in in_progress.items():
                if info["end"] == time:
                    completed.add(task_id)
                    completed_now.append(task_id)
                    available_resources += 1
            
            for task_id in completed_now:
                del in_progress[task_id]
    
    # クリティカルパスを計算
    def find_longest_path(task_id):
        if not dep_graph[task_id]:
            return [task_id]
        
        paths = []
        for dep in dep_graph[task_id]:
            path = find_longest_path(dep) + [task_id]
            paths.append(path)
        
        return max(paths, key=lambda p: sum(
            next(u["effort"] for u in implementation_units if u["id"] == t)
            for t in p
        ))
    
    # 最長パスを見つける
    all_paths = []
    for unit in implementation_units:
        if not any(unit["id"] in u["dependencies"] for u in implementation_units):
            # 終端タスクから逆算
            path = find_longest_path(unit["id"])
            all_paths.append(path)
    
    critical_path = max(all_paths, key=lambda p: sum(
        next(u["effort"] for u in implementation_units if u["id"] == t)
        for t in p
    )) if all_paths else []
    
    # 並列トラック数を計算
    parallel_tracks = []
    assigned = set()
    for unit in implementation_units:
        if unit["id"] not in assigned and not unit["dependencies"]:
            track = [unit["id"]]
            assigned.add(unit["id"])
            # このトラックに依存するタスクを追加
            for other in implementation_units:
                if other["id"] not in assigned and unit["id"] in other["dependencies"]:
                    track.append(other["id"])
                    assigned.add(other["id"])
            parallel_tracks.append(track)
    
    return {
        "total_duration": time,
        "critical_path": critical_path,
        "parallel_tracks": parallel_tracks
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])