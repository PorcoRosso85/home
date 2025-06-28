"""
Decision Service - 決定管理ユースケース
依存: domain層のみ
外部依存: なし
"""
from typing import List, Dict, Callable, Optional
from ..domain.types import Decision, DecisionResult, DecisionError, DecisionNotFoundError
from ..domain.decision import create_decision, calculate_similarity
from ..domain.embedder import create_embedding


# Repository型定義（依存性注入用）
DecisionRepository = Dict[str, Callable]


def create_decision_service(repository: DecisionRepository):
    """
    DecisionServiceを作成（依存性注入）
    
    Args:
        repository: save, find, find_all, searchメソッドを持つ辞書
    
    Returns:
        DecisionService関数の辞書
    """
    
    def add_decision(
        title: str,
        description: str
    ) -> DecisionResult:
        """新しい決定事項を追加"""
        # ID生成（簡易版）
        import time
        decision_id = f"req_{int(time.time() * 1000) % 1000000}"
        
        # 埋め込み生成
        embedding_result = create_embedding(f"{title} {description}")
        if "type" in embedding_result:
            return embedding_result
        
        # Decision作成
        decision_result = create_decision(
            id=decision_id,
            title=title,
            description=description,
            embedding=embedding_result
        )
        
        if "type" in decision_result:
            return decision_result
        
        # 保存
        save_result = repository["save"](decision_result)
        return save_result
    
    def find_decision(decision_id: str) -> DecisionResult:
        """IDで決定事項を検索"""
        return repository["find"](decision_id)
    
    def search_similar(
        query: str,
        threshold: float = 0.5,
        limit: int = 10
    ) -> List[Decision]:
        """類似する決定事項を検索"""
        # クエリの埋め込み生成
        query_embedding = create_embedding(query)
        if "type" in query_embedding:
            return []
        
        # 全決定事項を取得
        all_decisions = repository["find_all"]()
        
        # 類似度計算とフィルタリング
        results = []
        for decision in all_decisions:
            similarity = calculate_similarity(
                query_embedding,
                decision["embedding"]
            )
            if similarity >= threshold:
                results.append((similarity, decision))
        
        # ソートして上位を返す
        results.sort(key=lambda x: x[0], reverse=True)
        # 類似度を含めて返す
        return [{**decision, "similarity": sim} for sim, decision in results[:limit]]
    
    
    def list_all() -> List[Decision]:
        """全ての決定事項を取得"""
        return repository["find_all"]()
    
    return {
        "add_decision": add_decision,
        "find_decision": find_decision,
        "search_similar": search_similar,
        "list_all": list_all
    }

