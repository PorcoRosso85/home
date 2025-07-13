"""
シンプルな重複検出器
POC searchの代わりに基本的な文字列類似度で重複を検出
"""
from typing import List, Dict, Any
from difflib import SequenceMatcher


def check_duplicates_simple(conn, new_text: str, threshold: float = 0.7, exclude_id: str = None) -> List[Dict[str, Any]]:
    """
    既存の要件から重複を検出
    
    Args:
        conn: KuzuDBコネクション
        new_text: 検索対象テキスト
        threshold: 類似度の閾値
        exclude_id: 除外する要件ID（作成中の要件自身を除外）
        
    Returns:
        類似要件のリスト
    """
    try:
        # 既存の要件を取得
        result = conn.execute("MATCH (r:RequirementEntity) RETURN r.id, r.title, r.description")
        
        duplicates = []
        new_words = set(new_text.lower().split())
        
        while result.has_next():
            row = result.get_next()
            req_id, title, description = row
            
            # 作成中の要件自身は除外
            if exclude_id and req_id == exclude_id:
                continue
            
            # 既存要件のテキスト
            existing_text = f"{title or ''} {description or ''}"
            existing_words = set(existing_text.lower().split())
            
            # 単語ベースの類似度計算（日本語対応）
            common_words = new_words & existing_words
            if len(new_words) > 0:
                word_similarity = len(common_words) / len(new_words)
            else:
                word_similarity = 0
            
            # 文字列全体の類似度
            sequence_similarity = SequenceMatcher(None, new_text.lower(), existing_text.lower()).ratio()
            
            # 総合スコア（単語と文字列の平均）
            similarity = (word_similarity + sequence_similarity) / 2
            
            if similarity >= threshold:
                duplicates.append({
                    "id": req_id,
                    "title": title,
                    "description": description,
                    "score": round(similarity, 3),
                    "type": "simple_similarity"
                })
        
        # スコア順にソート
        duplicates.sort(key=lambda x: x["score"], reverse=True)
        return duplicates[:5]  # 上位5件
        
    except Exception as e:
        print(f"Duplicate check error: {str(e)}")
        return []