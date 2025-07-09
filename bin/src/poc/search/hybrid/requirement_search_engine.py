#!/usr/bin/env python3
"""
VSS/FTS統合検索エンジン
規約準拠: スコアリングなし、順位ベースの統合
"""

from typing import List, Dict, Any, Set


def hybrid_search(
    connection: Any,
    query: str,
    use_vss: bool = True,
    use_fts: bool = True,
    k: int = 10
) -> List[Dict[str, Any]]:
    """
    VSSとFTSを組み合わせた検索
    
    Args:
        connection: KuzuDB接続
        query: 検索クエリ
        use_vss: ベクトル検索を使用
        use_fts: キーワード検索を使用
        k: 返却する要件数
        
    Returns:
        統合された検索結果（順位のみ）
    """
    results_map: Dict[str, Dict[str, Any]] = {}
    sources_map: Dict[str, Set[str]] = {}
    
    # VSS検索
    if use_vss:
        try:
            from ..vss.similarity_search import search_similar_requirements
            vss_results = search_similar_requirements(connection, query, k)
            
            for result in vss_results:
                req_id = result["id"]
                if req_id not in results_map:
                    results_map[req_id] = result
                    sources_map[req_id] = set()
                sources_map[req_id].add("vss")
        except:
            pass
    
    # FTS検索
    if use_fts:
        try:
            from ..fts.keyword_search import search_by_keywords
            fts_results = search_by_keywords(connection, query)
            
            for result in fts_results:
                req_id = result["id"]
                if req_id not in results_map:
                    results_map[req_id] = result
                    sources_map[req_id] = set()
                sources_map[req_id].add("fts")
        except:
            pass
    
    # 結果の統合
    final_results = []
    
    # 複数ソースでマッチしたものを優先
    sorted_ids = sorted(
        results_map.keys(),
        key=lambda x: (len(sources_map[x]), x),
        reverse=True
    )
    
    for req_id in sorted_ids[:k]:
        result = results_map[req_id]
        result["sources"] = sorted(list(sources_map[req_id]))
        
        # ランク情報を削除（統合結果なので個別ランクは意味がない）
        if "similarity_rank" in result:
            del result["similarity_rank"]
            
        final_results.append(result)
    
    return final_results