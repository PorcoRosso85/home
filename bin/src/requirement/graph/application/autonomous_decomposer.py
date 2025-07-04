"""
Autonomous Decomposer - 自律的要件分解サービス
依存: domain
外部依存: なし
"""
from typing import Dict, List, Optional, Callable, Tuple
from datetime import datetime
from ..domain.types import Decision, DecisionResult
from ..domain.embedder import create_embedding
from ..infrastructure.variables.constants import AUTONOMOUS_MAX_DEPTH, AUTONOMOUS_TARGET_SIZE


# Repository型定義（依存性注入用）
DecomposerRepository = Dict[str, Callable]


def create_autonomous_decomposer(repository: DecomposerRepository):
    """
    自律的要件分解サービスを作成
    
    Args:
        repository: save, find, add_dependency, execute メソッドを持つ辞書
        
    Returns:
        DecomposerService関数の辞書
    """
    
    def decompose_requirement(
        requirement_id: str,
        decomposition_strategy: str = "hierarchical",
        max_depth: int = AUTONOMOUS_MAX_DEPTH,
        target_size: int = AUTONOMOUS_TARGET_SIZE
    ) -> Dict:
        """
        要件を自律的に分解
        
        Args:
            requirement_id: 分解対象の要件ID
            decomposition_strategy: "hierarchical" | "functional" | "temporal"
            max_depth: 最大分解深度
            target_size: 各レベルでの目標子要件数
            
        Returns:
            {
                "status": "success" | "error",
                "decomposed_count": int,
                "tree_structure": dict,
                "suggestions": list
            }
        """
        # 要件を取得
        req_result = repository["find"](requirement_id)
        if "type" in req_result and "Error" in req_result["type"]:
            return {
                "status": "error",
                "error": f"Requirement {requirement_id} not found"
            }
        
        requirement = req_result
        
        # すでに子要件があるかチェック
        existing_children = _get_existing_children(requirement_id)
        if existing_children:
            return {
                "status": "info",
                "message": "Requirement already has children",
                "existing_children": existing_children,
                "decomposed_count": 0
            }
        
        # 分解戦略に基づいて子要件を生成
        if decomposition_strategy == "hierarchical":
            sub_requirements = _decompose_hierarchical(requirement, target_size)
        elif decomposition_strategy == "functional":
            sub_requirements = _decompose_functional(requirement, target_size)
        elif decomposition_strategy == "temporal":
            sub_requirements = _decompose_temporal(requirement, target_size)
        else:
            return {
                "status": "error",
                "error": f"Unknown decomposition strategy: {decomposition_strategy}"
            }
        
        # 子要件を保存
        created_requirements = []
        for sub_req in sub_requirements:
            # IDを生成
            sub_req["id"] = f"{requirement_id}_{sub_req['suffix']}"
            sub_req["created_at"] = datetime.now()
            sub_req["embedding"] = create_embedding(f"{sub_req['title']} {sub_req['description']}")
            
            # 保存
            save_result = repository["save"](sub_req, parent_id=requirement_id)
            if "type" not in save_result or "Error" not in save_result["type"]:
                created_requirements.append(sub_req)
        
        # ツリー構造を構築
        tree_structure = _build_tree_structure(requirement, created_requirements)
        
        # 次のアクションを提案
        suggestions = _generate_next_suggestions(requirement_id, created_requirements)
        
        return {
            "status": "success",
            "decomposed_count": len(created_requirements),
            "tree_structure": tree_structure,
            "suggestions": suggestions
        }
    
    def analyze_decomposition_quality(requirement_id: str) -> Dict:
        """
        分解の品質を分析
        
        Args:
            requirement_id: 分析対象の要件ID
            
        Returns:
            品質メトリクス
        """
        # 進捗を計算するクエリ
        progress_query = """
        MATCH (r:RequirementEntity {id: $req_id})
        OPTIONAL MATCH (child:RequirementEntity)-[:DEPENDS_ON*]->(r)
        WITH r, count(child) as child_count
        RETURN child_count as count
        """
        progress_result = repository["execute"](progress_query, {"req_id": requirement_id})
        
        # 制約違反チェック（簡易版）
        constraint_result = {"status": "success", "valid": True}
        
        # 品質メトリクスを計算
        metrics = {
            "completeness": 0.0,
            "balance": 0.0,
            "coverage": 0.0,
            "issues": []
        }
        
        # QueryResultから子要件の数を取得
        child_count = 0
        if progress_result.has_next():
            child_count = progress_result.get_next()[0]
        
        # 完全性: 子要件の数が適切か
        if 3 <= child_count <= 7:
            metrics["completeness"] = 1.0
        else:
            metrics["completeness"] = max(0.0, 1.0 - abs(child_count - 5) * 0.2)
        
        # 進捗（簡易版：全て未完了と仮定）
        metrics["progress"] = 0.0
        
        if constraint_result["status"] == "success" and constraint_result.get("data"):
            is_valid, violations = constraint_result["data"][0]
            if not is_valid:
                metrics["issues"].extend(violations)
        
        # バランスチェック（子要件の複雑さが均等か）
        children = _get_existing_children(requirement_id)
        if children:
            # 簡易的にタイトル長でバランスを評価
            title_lengths = [len(c["title"]) for c in children]
            if title_lengths:
                avg_length = sum(title_lengths) / len(title_lengths)
                variance = sum((l - avg_length) ** 2 for l in title_lengths) / len(title_lengths)
                metrics["balance"] = max(0.0, 1.0 - variance / 100)  # 正規化
        
        return metrics
    
    def suggest_refinements(requirement_id: str) -> List[Dict]:
        """
        分解の改善提案を生成
        
        Args:
            requirement_id: 対象要件ID
            
        Returns:
            改善提案のリスト
        """
        refinements = []
        
        # 品質分析
        quality = analyze_decomposition_quality(requirement_id)
        
        # 完全性が低い場合
        if quality["completeness"] < 0.8:
            children = _get_existing_children(requirement_id)
            child_count = len(children)
            
            if child_count < 3:
                refinements.append({
                    "type": "add_children",
                    "reason": "Too few sub-requirements",
                    "suggestion": f"Add {3 - child_count} more sub-requirements for better coverage"
                })
            elif child_count > 7:
                refinements.append({
                    "type": "merge_children",
                    "reason": "Too many sub-requirements",
                    "suggestion": "Consider merging related sub-requirements"
                })
        
        # バランスが悪い場合
        if quality["balance"] < 0.7:
            refinements.append({
                "type": "rebalance",
                "reason": "Unbalanced complexity",
                "suggestion": "Redistribute complexity evenly across sub-requirements"
            })
        
        # 制約違反がある場合
        if quality["issues"]:
            for issue in quality["issues"]:
                if "circular" in issue:
                    refinements.append({
                        "type": "fix_circular",
                        "reason": "Circular dependency detected",
                        "suggestion": "Remove circular dependencies"
                    })
                elif "depth" in issue:
                    refinements.append({
                        "type": "flatten_hierarchy",
                        "reason": "Hierarchy too deep",
                        "suggestion": "Consider flattening the requirement hierarchy"
                    })
        
        return refinements
    
    def _decompose_hierarchical(requirement: Decision, target_size: int) -> List[Dict]:
        """階層的分解（抽象から具体へ）"""
        sub_requirements = []
        
        # 要件の深さに基づいて分解戦略を決定
        # 深さ0-1: 高レベルアーキテクチャ分解
        # 深さ2-3: 中レベル設計分解
        # 深さ4+: 詳細実装分解
        
        # 親要件の深さを推定（本来はRELATIONで判定）
        # TODO: repository.get_depth(requirement_id) で実際の深さを取得
        depth = 0  # デフォルト深さ
        
        if depth <= 1:
            # 高レベル分解
            aspects = ["architecture", "implementation", "testing", "deployment", "monitoring"]
        elif depth <= 3:
            # 中レベル分解
            aspects = ["design", "development", "validation", "integration"]
        else:
            # 詳細分解
            aspects = ["core", "interface", "data", "security", "performance"]
        
        # 必要な数だけ選択
        selected_aspects = aspects[:min(target_size, len(aspects))]
        
        for i, aspect in enumerate(selected_aspects):
            sub_req = {
                "suffix": f"{aspect}_{i+1:02d}",
                "title": f"{requirement['title']} - {aspect.capitalize()}",
                "description": f"{aspect.capitalize()} aspects of {requirement['description']}",
                "status": "proposed",
                "decomposition_aspect": aspect
            }
                
            sub_requirements.append(sub_req)
        
        return sub_requirements
    
    def _decompose_functional(requirement: Decision, target_size: int) -> List[Dict]:
        """機能的分解（機能単位で分割）"""
        # タイトルと説明から機能を推測
        title_words = requirement["title"].lower().split()
        
        # 一般的な機能パターン
        if any(word in title_words for word in ["api", "service", "interface"]):
            functions = ["authentication", "validation", "processing", "response", "logging"]
        elif any(word in title_words for word in ["database", "storage", "data"]):
            functions = ["schema", "migration", "backup", "optimization", "access"]
        elif any(word in title_words for word in ["ui", "frontend", "display"]):
            functions = ["layout", "interaction", "styling", "navigation", "responsive"]
        else:
            functions = ["input", "process", "output", "error_handling", "monitoring"]
        
        sub_requirements = []
        selected_functions = functions[:min(target_size, len(functions))]
        
        for i, func in enumerate(selected_functions):
            sub_requirements.append({
                "suffix": f"func_{func}_{i+1:02d}",
                "title": f"{requirement['title']} - {func.replace('_', ' ').title()}",
                "description": f"Handle {func.replace('_', ' ')} for {requirement['description']}",
                "status": "proposed",
                "function_area": func  # TODO: RELATIONで表現
            })
        
        return sub_requirements
    
    def _decompose_temporal(requirement: Decision, target_size: int) -> List[Dict]:
        """時系列分解（フェーズやステップで分割）"""
        phases = ["planning", "design", "implementation", "testing", "deployment", "maintenance"]
        
        sub_requirements = []
        selected_phases = phases[:min(target_size, len(phases))]
        
        for i, phase in enumerate(selected_phases):
            sub_requirements.append({
                "suffix": f"phase_{i+1:02d}_{phase}",
                "title": f"{requirement['title']} - Phase {i+1}: {phase.capitalize()}",
                "description": f"{phase.capitalize()} phase for {requirement['description']}",
                "status": "proposed",
                "phase": f"phase_{i+1}_{phase}"  # TODO: RELATIONで表現
            })
        
        # フェーズ間の依存関係を後で追加
        return sub_requirements
    
    def _get_existing_children(requirement_id: str) -> List[Dict]:
        """既存の子要件を取得"""
        # 子要件を取得するクエリ
        children_query = """
        MATCH (parent:RequirementEntity {id: $parent_id})
        MATCH (child:RequirementEntity)-[:DEPENDS_ON]->(parent)
        RETURN child.id as id, child.title as title, child.description as description
        """
        result = repository["execute"](children_query, {"parent_id": requirement_id})
        
        children = []
        while result.has_next():
            row = result.get_next()
            children.append({
                "id": row[0],
                "title": row[1],
                "description": row[2]
            })
        return children
    
    def _build_tree_structure(parent: Decision, children: List[Dict]) -> Dict:
        """ツリー構造を構築"""
        return {
            "id": parent["id"],
            "title": parent["title"],
            "type": "parent",
            "children": [
                {
                    "id": child["id"],
                    "title": child["title"],
                    "type": "child",
                    "hierarchy_info": child.get("hierarchy_level", "")
                }
                for child in children
            ]
        }
    
    def _generate_next_suggestions(parent_id: str, children: List[Dict]) -> List[Dict]:
        """次のアクション提案を生成"""
        suggestions = []
        
        # 各子要件をさらに分解することを提案
        if len(children) <= 5:  # 管理可能な数の場合
            for child in children[:2]:  # 最初の2つのみ
                suggestions.append({
                    "action": "decompose_child",
                    "target": child["id"],
                    "reason": f"Further decompose '{child['title']}' for detailed planning"
                })
        
        # 依存関係の設定を提案
        if len(children) > 1:
            # 時系列タグがある場合は順序依存を提案
            phase_children = [c for c in children if "phase" in c]
            if len(phase_children) > 1:
                suggestions.append({
                    "action": "add_dependencies",
                    "type": "sequential",
                    "targets": [c["id"] for c in phase_children],
                    "reason": "Add phase dependencies for proper execution order"
                })
        
        return suggestions
    
    return {
        "decompose_requirement": decompose_requirement,
        "analyze_decomposition_quality": analyze_decomposition_quality,
        "suggest_refinements": suggest_refinements
    }
