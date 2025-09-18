"""ドメインサービス（純粋関数）"""

from typing import List, Tuple, Dict
import math
from .types import RequirementDict, RelationDict, EmbeddingDict, create_embedding, create_requirement


def calculate_similarity(emb1: EmbeddingDict, emb2: EmbeddingDict) -> float:
    """2つの埋め込み間の類似度を計算（コサイン類似度）"""
    if emb1["dimension"] != emb2["dimension"]:
        raise ValueError(f"Dimension mismatch: {emb1['dimension']} != {emb2['dimension']}")
    
    vec1 = emb1["vector"]
    vec2 = emb2["vector"]
    
    # ドット積
    dot_product = sum(v1 * v2 for v1, v2 in zip(vec1, vec2))
    
    # ノルム
    norm1 = math.sqrt(sum(v * v for v in vec1))
    norm2 = math.sqrt(sum(v * v for v in vec2))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(dot_product / (norm1 * norm2))


def calculate_uniqueness_score(
    target_embedding: EmbeddingDict,
    similar_requirements: List[RequirementDict]
) -> float:
    """独自性スコアを計算（1.0 = 完全に独自、0.0 = 重複）"""
    if not similar_requirements:
        return 1.0
    
    max_similarity = 0.0
    for req in similar_requirements:
        similarity = calculate_similarity(target_embedding, req["embedding"])
        max_similarity = max(max_similarity, similarity)
    
    # 独自性は最大類似度の逆
    return 1.0 - max_similarity


def calculate_clarity_score(requirement_text: str) -> float:
    """明確性スコアを計算（簡易版）"""
    # 簡易実装: 文字数で判定（日本語対応）
    if not requirement_text:
        return 0.0
    
    char_count = len(requirement_text)
    
    # 適度な長さが高スコア（日本語は文字数で判定）
    if 10 <= char_count <= 100:
        clarity = 0.9
    elif char_count < 5:
        clarity = 0.3  # 短すぎる
    elif char_count > 200:
        clarity = 0.5  # 長すぎる
    else:
        clarity = 0.7
    
    # 曖昧な表現のペナルティ
    vague_words = ["など", "等", "色々", "いろいろ", "適当", "それなり"]
    for word in vague_words:
        if word in requirement_text:
            clarity *= 0.8
    
    return clarity


def calculate_completeness_score(requirement_text: str) -> float:
    """完全性スコアを計算（簡易版）"""
    # 必須要素のチェック
    score = 0.0
    elements = {
        "what": ["機能", "処理", "動作", "を"],  # 何を
        "who": ["ユーザー", "管理者", "システム", "が"],  # 誰が
        "condition": ["場合", "とき", "時", "際"],  # 条件
    }
    
    for element_type, keywords in elements.items():
        if any(keyword in requirement_text for keyword in keywords):
            score += 0.33
    
    return min(score, 1.0)


def rank_by_similarity(
    target: RequirementDict,
    candidates: List[RequirementDict]
) -> List[Tuple[RequirementDict, float]]:
    """類似度で要件をランク付け"""
    scored = []
    for candidate in candidates:
        if candidate["id"] == target["id"]:
            continue
        similarity = calculate_similarity(target["embedding"], candidate["embedding"])
        scored.append((candidate, similarity))
    
    return sorted(scored, key=lambda x: x[1], reverse=True)


def filter_high_confidence_relations(
    relations: List[RelationDict],
    threshold: float
) -> List[RelationDict]:
    """高信頼度の関係のみをフィルタ"""
    if not 0.0 <= threshold <= 1.0:
        raise ValueError(f"Threshold must be between 0 and 1, got {threshold}")
    
    return [rel for rel in relations if rel["confidence"] >= threshold]


def generate_suggestions(
    requirement: RequirementDict,
    similar_requirements: List[RequirementDict],
    scores: Dict[str, float]
) -> List[str]:
    """要件に対する提案を生成"""
    suggestions = []
    
    # 独自性が低い場合
    if scores.get("uniqueness", 1.0) < 0.5:
        if similar_requirements:
            similar_text = similar_requirements[0]["text"]
            suggestions.append(
                f"類似要件「{similar_text}」が存在します。関係を定義するか、差分を明確化してください"
            )
    
    # 明確性が低い場合
    if scores.get("clarity", 1.0) < 0.6:
        suggestions.append("要件をより具体的に記述してください（5-20単語が推奨）")
    
    # 完全性が低い場合
    if scores.get("completeness", 1.0) < 0.7:
        suggestions.append("「誰が」「何を」「どのような条件で」を明記してください")
    
    return suggestions


# ===== テストコード（規約: in-sourceテスト） =====

def test_calculate_similarity_identical_vectors_returns_one():
    """類似度計算_同一ベクトル_1を返す"""
    emb1 = create_embedding([1.0, 0.0, 0.0])
    emb2 = create_embedding([1.0, 0.0, 0.0])
    assert calculate_similarity(emb1, emb2) == 1.0


def test_calculate_similarity_orthogonal_vectors_returns_zero():
    """類似度計算_直交ベクトル_0を返す"""
    emb1 = create_embedding([1.0, 0.0, 0.0])
    emb2 = create_embedding([0.0, 1.0, 0.0])
    assert calculate_similarity(emb1, emb2) == 0.0


def test_calculate_similarity_dimension_mismatch_raises_error():
    """類似度計算_次元不一致_エラー発生"""
    emb1 = create_embedding([1.0, 0.0])
    emb2 = create_embedding([1.0, 0.0, 0.0])
    try:
        calculate_similarity(emb1, emb2)
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "dimension mismatch" in str(e).lower()


def test_uniqueness_score_no_similar_returns_one():
    """独自性スコア_類似なし_1を返す"""
    target_emb = create_embedding([1.0, 0.0, 0.0])
    similar = []
    score = calculate_uniqueness_score(target_emb, similar)
    assert score == 1.0


def test_uniqueness_score_has_duplicate_returns_low_score():
    """独自性スコア_重複あり_低スコア"""
    target_emb = create_embedding([1.0, 0.0, 0.0])
    similar = [create_requirement("既存要件", target_emb)]  # 同じ埋め込み
    score = calculate_uniqueness_score(target_emb, similar)
    assert score == 0.0  # 完全重複


def test_uniqueness_score_has_similar_returns_medium_score():
    """独自性スコア_類似あり_中スコア"""
    target_emb = create_embedding([1.0, 0.0, 0.0])
    # 少し違うベクトル（コサイン類似度約0.7）
    similar_emb = create_embedding([1.0, 1.0, 0.0])
    similar = [create_requirement("類似要件", similar_emb)]
    score = calculate_uniqueness_score(target_emb, similar)
    assert 0.2 < score < 0.4  # 中程度のスコア


def test_clarity_score_good_length_returns_high_score():
    """明確性スコア_適切な長さ_高スコア"""
    text = "ユーザー認証機能を実装する"
    score = calculate_clarity_score(text)
    assert score > 0.8


def test_clarity_score_too_short_returns_low_score():
    """明確性スコア_短すぎる_低スコア"""
    score = calculate_clarity_score("認証")
    assert score < 0.5


def test_clarity_score_vague_words_returns_reduced_score():
    """明確性スコア_曖昧な表現_減点"""
    clear_text = "ユーザー認証機能を実装する"
    vague_text = "ユーザー認証機能などを実装する"
    
    clear_score = calculate_clarity_score(clear_text)
    vague_score = calculate_clarity_score(vague_text)
    
    assert vague_score < clear_score


def test_completeness_score_all_elements_returns_high_score():
    """完全性スコア_全要素あり_高スコア"""
    text = "ユーザーがログイン画面で認証情報を入力した場合、システムは認証処理を実行する"
    score = calculate_completeness_score(text)
    assert score > 0.9


def test_completeness_score_missing_elements_returns_low_score():
    """完全性スコア_要素不足_低スコア"""
    score = calculate_completeness_score("認証する")
    assert score < 0.5


def test_filter_relations_valid_threshold_returns_filtered():
    """関係フィルタ_有効閾値_フィルタ済みリスト"""
    from datetime import datetime
    
    relations: List[RelationDict] = [
        {
            "from_id": "REQ-001",
            "to_id": "REQ-002",
            "relation_type": "depends_on",
            "confidence": 0.9,
            "inferred_at": datetime.now(),
            "reasoning": "高信頼"
        },
        {
            "from_id": "REQ-001",
            "to_id": "REQ-003",
            "relation_type": "related_to",
            "confidence": 0.3,
            "inferred_at": datetime.now(),
            "reasoning": "低信頼"
        },
    ]
    
    filtered = filter_high_confidence_relations(relations, 0.5)
    assert len(filtered) == 1
    assert filtered[0]["confidence"] == 0.9


def test_generate_suggestions_low_uniqueness_returns_duplicate_warning():
    """提案生成_低独自性_重複警告"""
    req = create_requirement("ユーザー認証")
    similar = [create_requirement("ユーザー認証機能")]
    scores = {"uniqueness": 0.3}
    
    suggestions = generate_suggestions(req, similar, scores)
    assert len(suggestions) > 0
    assert "類似要件" in suggestions[0]
    assert "ユーザー認証機能" in suggestions[0]