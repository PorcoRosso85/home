"""
Custom Procedures - Cypher拡張プロシージャ
依存: domain
外部依存: kuzu
"""
from typing import Dict, List, Any, Optional, Tuple
import json


class CustomProcedures:
    """
    Cypherクエリから呼び出されるカスタムプロシージャ
    CALL requirement.score() などの形式で利用
    """
    
    def __init__(self, connection):
        self.connection = connection
        self.procedures = {
            "requirement.score": self.score_requirement,
            "requirement.progress": self.calculate_progress,
            "requirement.validate": self.validate_constraints,
            "requirement.impact": self.analyze_impact,
            "requirement.suggest_decomposition": self.suggest_decomposition
        }
    
    def register_all(self):
        """すべてのプロシージャを登録"""
        # KuzuDBではカスタムプロシージャの登録は別途必要
        # ここでは登録済みと仮定
        return True
    
    def find_similar_requirements(
        self,
        requirement_id: str,
        query_text: str
    ) -> List[Dict]:
        """
        類似要件を検索（スコアリングは行わない）
        
        Args:
            requirement_id: 対象要件ID
            query_text: 比較用テキスト
            
        Returns:
            類似要件のリスト
        """
        return self._find_similar(requirement_id, query_text)
    
    def _find_similar(self, requirement_id: str, query_text: str) -> List[Dict]:
        """類似要件を検索"""
        if not query_text:
            return []
        
        # クエリの埋め込みを生成（簡易版）
        query_embedding = self._create_simple_embedding(query_text)
        
        # すべての要件を取得して類似度計算
        all_result = self.connection.execute("MATCH (r:RequirementEntity) RETURN r")
        similar_reqs = []
        
        while all_result.has_next():
            req = all_result.get_next()[0]
            if req["id"] != requirement_id:
                similarity = self._calculate_similarity(query_embedding, req["embedding"])
                if similarity > 0.3:  # 閾値
                    similar_reqs.append({
                        "id": req["id"],
                        "title": req["title"],
                        "similarity": similarity
                    })
        
        # 類似度でソート
        similar_reqs.sort(key=lambda x: x["similarity"], reverse=True)
        
        # 上位5件を返す
        return similar_reqs[:5]
    
    def check_constraint_violations(self, requirement_id: str) -> Dict[str, List[str]]:
        """制約違反をチェック（スコアリングは行わない）"""
        violations = []
        
        # 循環依存チェック
        circular_check = self.connection.execute("""
            MATCH path = (start:RequirementEntity {id: $req_id})-[:DEPENDS_ON*]->(end:RequirementEntity)
            WHERE end.id = $req_id
            RETURN path
        """, {"req_id": requirement_id})
        
        if circular_check.has_next():
            violations.append("circular_dependency")
        
        # 深度チェック（5階層以上は警告）
        depth_check = self.connection.execute("""
            MATCH path = (root)-[:PARENT_OF*]->(r:RequirementEntity {id: $req_id})
            RETURN length(path) as depth
            ORDER BY depth DESC
            LIMIT 1
        """, {"req_id": requirement_id})
        
        if depth_check.has_next():
            depth = depth_check.get_next()[0]
            if depth > 5:
                violations.append(f"deep_hierarchy: {depth}")
        
        return {"violations": violations}
    
    def get_impact_analysis(self, requirement_id: str) -> Dict[str, Any]:
        """影響度分析（スコアリングは行わない）"""
        # この要件に依存している要件数を数える
        dependent_result = self.connection.execute("""
            MATCH (r:RequirementEntity)-[:DEPENDS_ON]->(target:RequirementEntity {id: $req_id})
            RETURN count(r) as dependent_count
        """, {"req_id": requirement_id})
        
        dependent_count = 0
        if dependent_result.has_next():
            dependent_count = dependent_result.get_next()[0]
        
        return {"dependent_count": dependent_count}
    
    def _create_simple_embedding(self, text: str) -> List[float]:
        """簡易的な埋め込みベクトル生成"""
        embedding = [0.1] * 50
        for i, char in enumerate(text[:50]):
            embedding[i % 50] += ord(char) / 1000.0
        
        # 正規化
        norm = sum(x*x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
    
    def _calculate_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """コサイン類似度計算"""
        if len(emb1) != len(emb2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(emb1, emb2))
        return max(0.0, min(1.0, dot_product))  # 0-1の範囲に制限
    
    def calculate_progress(
        self,
        requirement_id: str,
        include_children: bool = True
    ) -> List[Tuple[str, Any]]:
        """
        要件の進捗を計算
        
        Args:
            requirement_id: 対象要件ID
            include_children: 子要件を含めるか
            
        Returns:
            [(progress, details), ...] の形式で結果を返す
        """
        if not include_children:
            # 単体の進捗のみ
            result = self.connection.execute(
                "MATCH (r:RequirementEntity {id: $req_id}) RETURN r.status",
                {"req_id": requirement_id}
            )
            
            if result.has_next():
                status = result.get_next()[0]
                progress = 1.0 if status == "completed" else 0.0
                return [(progress, {"status": status, "completed_count": 1 if progress else 0, "total_count": 1})]
            
            return [(0.0, {"error": "Requirement not found"})]
        
        # 子要件を含めた進捗計算
        children_result = self.connection.execute("""
            MATCH (parent:RequirementEntity {id: $parent_id})-[:PARENT_OF]->(child:RequirementEntity)
            RETURN child.status
        """, {"parent_id": requirement_id})
        
        statuses = []
        while children_result.has_next():
            statuses.append(children_result.get_next()[0])
        
        if not statuses:
            # 子要件がない場合は自身の状態のみ
            self_result = self.connection.execute(
                "MATCH (r:RequirementEntity {id: $req_id}) RETURN r.status",
                {"req_id": requirement_id}
            )
            if self_result.has_next():
                status = self_result.get_next()[0]
                progress = 1.0 if status == "completed" else 0.0
                return [(progress, {"status": status, "completed_count": 1 if progress else 0, "total_count": 1})]
        
        # 完了率を計算
        completed_count = sum(1 for s in statuses if s == "completed")
        total_count = len(statuses)
        progress = completed_count / total_count if total_count > 0 else 0.0
        
        return [(progress, {
            "completed_count": completed_count,
            "total_count": total_count,
            "completion_rate": f"{progress * 100:.1f}%"
        })]
    
    def validate_constraints(
        self,
        requirement_id: str,
        operation: str,
        target_id: Optional[str] = None
    ) -> List[Tuple[str, Any]]:
        """
        制約違反をチェック
        
        Args:
            requirement_id: 対象要件ID
            operation: "add_dependency" | "add_child" | "delete"
            target_id: 操作対象ID（依存先や親など）
            
        Returns:
            [(is_valid, violations), ...] の形式で結果を返す
        """
        violations = []
        
        if operation == "add_dependency" and target_id:
            # 循環依存チェック
            # target_id -> requirement_idへの経路があるか確認
            path_check = self.connection.execute("""
                MATCH path = (start:RequirementEntity {id: $target_id})-[:DEPENDS_ON*]->(end:RequirementEntity {id: $req_id})
                RETURN count(path) > 0 as has_path
            """, {"target_id": target_id, "req_id": requirement_id})
            
            if path_check.has_next() and path_check.get_next()[0]:
                violations.append("circular_dependency")
            
        elif operation == "add_child" and target_id:
            # 階層深度チェック
            depth_check = self.connection.execute("""
                MATCH path = (root)-[:PARENT_OF*]->(parent:RequirementEntity {id: $req_id})
                RETURN length(path) as depth
                ORDER BY depth DESC
                LIMIT 1
            """, {"req_id": requirement_id})
            
            current_depth = 0
            if depth_check.has_next():
                current_depth = depth_check.get_next()[0]
            
            if current_depth >= 5:  # 5階層以上は警告
                violations.append(f"max_depth_exceeded: {current_depth + 1}")
        
        elif operation == "delete":
            # 依存要件チェック
            dependent_check = self.connection.execute("""
                MATCH (r:RequirementEntity)-[:DEPENDS_ON]->(target:RequirementEntity {id: $req_id})
                RETURN count(r) as dependent_count
            """, {"req_id": requirement_id})
            
            if dependent_check.has_next():
                count = dependent_check.get_next()[0]
                if count > 0:
                    violations.append(f"has_dependent_requirements: {count}")
        
        is_valid = len(violations) == 0
        return [(is_valid, violations)]
    
    def analyze_impact(
        self,
        requirement_id: str,
        change_type: str = "modify"
    ) -> Dict[str, Any]:
        """
        変更の影響範囲を分析（スコアリングは行わない）
        
        Args:
            requirement_id: 対象要件ID
            change_type: "modify" | "delete" | "complete"
            
        Returns:
            影響分析結果の辞書
        """
        affected = []
        
        # 依存している要件を取得
        query = """
            MATCH (r:RequirementEntity)-[:DEPENDS_ON]->(target:RequirementEntity {id: $req_id})
            RETURN r
        """
        dependent_result = self.connection.execute(query, {"req_id": requirement_id})
        
        while dependent_result.has_next():
            req = dependent_result.get_next()[0]
            affected.append({
                "id": req["id"],
                "title": req["title"],
                "impact_type": "dependency"
            })
        
        # 子要件を取得（deleteやcompleteの場合）
        if change_type in ["delete", "complete"]:
            children_result = self.connection.execute("""
                MATCH (parent:RequirementEntity {id: $req_id})-[:PARENT_OF]->(child:RequirementEntity)
                RETURN child
            """, {"req_id": requirement_id})
            
            while children_result.has_next():
                req = children_result.get_next()[0]
                affected.append({
                    "id": req["id"],
                    "title": req["title"],
                    "impact_type": "parent_child"
                })
        
        return {
            "affected_requirements": affected,
            "affected_count": len(affected)
        }
    
    def suggest_decomposition(
        self,
        requirement_id: str,
        strategy: str = "hierarchical",
        target_count: int = 3
    ) -> List[Dict[str, Any]]:
        """
        要件の分解を提案
        
        Args:
            requirement_id: 分解対象の要件ID
            strategy: "hierarchical" | "functional" | "temporal"
            target_count: 提案する子要件の数
            
        Returns:
            分解提案のリスト
        """
        # 対象要件を取得
        req_result = self.connection.execute(
            "MATCH (r:RequirementEntity {id: $req_id}) RETURN r",
            {"req_id": requirement_id}
        )
        
        if not req_result.has_next():
            return []
        
        requirement = req_result.get_next()[0]
        suggestions = []
        
        # 戦略に基づいて分解案を生成
        if strategy == "hierarchical":
            # 親要件から子要件への階層的分解
            aspects = ["architecture", "implementation", "testing"]
            for i, aspect in enumerate(aspects[:target_count]):
                suggestions.append({
                    "parent_id": requirement_id,
                    "title": f"{requirement['title']} - {aspect.capitalize()}",
                    "create_query": """
                        CREATE (r:RequirementEntity {
                            id: $id,
                            title: $title,
                            status: 'proposed'
                        })
                        WITH r
                        MATCH (parent:RequirementEntity {id: $parent_id})
                        CREATE (parent)-[:PARENT_OF]->(r)
                        RETURN r
                    """,
                    "parameters": {
                        "id": f"{requirement_id}_{aspect}",
                        "title": f"{requirement['title']} - {aspect.capitalize()}",
                        "parent_id": requirement_id
                    }
                })
        
        return suggestions
    
    def score_requirement(
        self,
        requirement_id: str,
        requirement_data: Dict[str, Any]
    ) -> List[Tuple[float, str]]:
        """
        要件のスコアを計算（最小限の実装）
        
        Args:
            requirement_id: 要件ID
            requirement_data: 要件データ
            
        Returns:
            [(score, message), ...] の形式でスコアと説明を返す
        """
        # 最小限の実装：常に正常なスコアを返す
        return [(0.0, "No violations detected")]