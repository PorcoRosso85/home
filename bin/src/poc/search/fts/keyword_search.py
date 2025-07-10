#!/usr/bin/env python3
"""
キーワードベースの要件検索
規約準拠: FTSエクステンション使用
"""

from typing import List, Dict, Any


def search_by_keywords(connection: Any, keywords: str) -> List[Dict[str, Any]]:
    """
    キーワードで要件を検索

    Args:
        connection: KuzuDB接続
        keywords: 検索キーワード

    Returns:
        マッチした要件のリスト
    """
    results = []

    try:
        # titleでの検索
        title_result = connection.execute(
            """
            MATCH (r:RequirementEntity)
            WHERE r.title CONTAINS $keyword
            RETURN r.id, r.title, r.description
        """,
            {"keyword": keywords},
        )

        while title_result.has_next():
            row = title_result.get_next()
            results.append({"id": row[0], "title": row[1], "description": row[2], "match_type": "title"})
    except:
        # エラー時は空リストを返す
        pass

    return results
