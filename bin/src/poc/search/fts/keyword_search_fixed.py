#!/usr/bin/env python3
"""
KuzuDB仕様準拠のFTS実装
"""

from typing import List, Dict, Any


def create_fts_index(connection: Any, rebuild: bool = False) -> bool:
    """
    FTSインデックスを作成（KuzuDB仕様準拠）
    
    Returns:
        成功した場合True
    """
    try:
        # FTSエクステンションのインストール
        try:
            connection.execute("LOAD EXTENSION FTS;")
        except:
            connection.execute("INSTALL FTS;")
            connection.execute("LOAD EXTENSION FTS;")
        
        # 既存インデックスの削除（rebuildの場合）
        if rebuild:
            try:
                connection.execute("CALL DROP_FTS_INDEX('RequirementEntity', 'requirement_fts_index');")
            except:
                pass  # インデックスが存在しない場合
        
        # インデックス作成
        connection.execute("""
            CALL CREATE_FTS_INDEX(
                'RequirementEntity',
                'requirement_fts_index',
                ['title', 'description', 'acceptance_criteria']
            );
        """)
        
        return True
    except Exception as e:
        print(f"Warning: FTS index creation failed: {e}")
        return False


def search_by_keywords_with_fts(
    connection: Any,
    keywords: str,
    conjunctive: bool = False
) -> List[Dict[str, Any]]:
    """
    FTS拡張を使用したキーワード検索（KuzuDB仕様準拠）
    
    Args:
        connection: KuzuDB接続
        keywords: 検索キーワード
        conjunctive: True=AND検索、False=OR検索
        
    Returns:
        マッチした要件のリスト
    """
    try:
        # FTS検索実行
        result = connection.execute("""
            CALL QUERY_FTS_INDEX(
                'RequirementEntity',
                'requirement_fts_index',
                $query,
                conjunctive := $conjunctive
            ) RETURN node, score;
        """, {
            "query": keywords,
            "conjunctive": conjunctive
        })
        
        # 結果を収集（スコアは使用しない）
        results = []
        while result.has_next():
            row = result.get_next()
            node = row[0]
            # score = row[1]  # 使用しない（スコアリングなし）
            
            results.append({
                "id": node["id"],
                "title": node.get("title", ""),
                "description": node.get("description", ""),
                "match_type": "fts"
            })
        
        return results
        
    except Exception as e:
        # フォールバック：CONTAINS使用
        print(f"FTS search failed, using fallback: {e}")
        return search_by_keywords_fallback(connection, keywords)


def search_by_keywords_fallback(
    connection: Any,
    keywords: str
) -> List[Dict[str, Any]]:
    """
    フォールバック：CONTAINSによるキーワード検索
    """
    results = []
    
    try:
        # titleでの検索
        title_result = connection.execute("""
            MATCH (r:RequirementEntity)
            WHERE r.title CONTAINS $keyword
            RETURN r.id, r.title, r.description
        """, {"keyword": keywords})
        
        while title_result.has_next():
            row = title_result.get_next()
            results.append({
                "id": row[0],
                "title": row[1] or "",
                "description": row[2] or "",
                "match_type": "title"
            })
        
        # descriptionでの検索（重複除外）
        existing_ids = {r["id"] for r in results}
        
        desc_result = connection.execute("""
            MATCH (r:RequirementEntity)
            WHERE r.description CONTAINS $keyword
            RETURN r.id, r.title, r.description
        """, {"keyword": keywords})
        
        while desc_result.has_next():
            row = desc_result.get_next()
            if row[0] not in existing_ids:
                results.append({
                    "id": row[0],
                    "title": row[1] or "",
                    "description": row[2] or "",
                    "match_type": "description"
                })
    except:
        pass
    
    return results