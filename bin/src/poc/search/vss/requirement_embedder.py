#!/usr/bin/env python3
"""
要件エンティティの埋め込み生成
規約準拠: パス操作なし、関数型実装
"""

from typing import List, Dict

# WARN: Mock実装（sentence_transformersなしで動作）
# TODO: 本番環境ではsentence_transformersを使用すること
def generate_requirement_embedding(requirement: Dict) -> List[float]:
    """
    要件から埋め込みベクトルを生成
    
    Args:
        requirement: 要件データ（title, description, acceptance_criteria）
        
    Returns:
        384次元の埋め込みベクトル
    """
    # テスト用のモック実装
    # 実際のsentence_transformersが利用可能になったら置き換え
    text_parts = []
    
    if "title" in requirement:
        text_parts.append(requirement["title"])
    
    if "description" in requirement:
        text_parts.append(requirement["description"])
        
    if "acceptance_criteria" in requirement:
        text_parts.append(requirement["acceptance_criteria"])
    
    # 簡易的な384次元ベクトル生成
    combined_text = " ".join(text_parts)
    hash_value = hash(combined_text)
    
    # 擬似ランダムな384次元ベクトル
    embedding = []
    for i in range(384):
        # ハッシュ値を使って擬似的な値を生成
        value = ((hash_value + i) % 1000) / 1000.0
        embedding.append(value)
    
    return embedding