#!/usr/bin/env python3
"""
ドメイン層 - 純粋関数によるビジネスロジック

ベクトル検索に関する以下のビジネスロジックを純粋関数として実装:
- 類似度計算（コサイン類似度）
- 距離からスコアへの変換
- 検索結果のソート
- 上位k件の選択
"""

from dataclasses import dataclass
from enum import Enum

import numpy as np

# ============================================================================
# Data Classes - Immutable domain entities
# ============================================================================


# VSS SearchResult class removed - VSS functionality deprecated


@dataclass(frozen=True)
class FTSSearchResult:
    """全文検索結果の不変データクラス

    Attributes:
        id: ドキュメントの一意識別子
        content: ドキュメントの内容
        score: 関連性スコア
        highlights: ハイライトされたテキストフラグメントのタプル
        position_info: 一致位置情報のタプル (開始位置, 終了位置)
    """

    id: str
    content: str
    score: float
    highlights: tuple[str, ...]
    position_info: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class IndexResult:
    """インデックス作成結果の不変データクラス

    Attributes:
        document_id: インデックスされたドキュメントのID
        success: インデックス作成の成否
        tokens_count: トークン数
        index_time_ms: インデックス作成時間（ミリ秒）
        error: エラーメッセージ（エラー時のみ）
    """

    document_id: str
    success: bool
    tokens_count: int
    index_time_ms: float
    error: str | None


# ============================================================================
# Enumerations - Domain-specific enumerations
# ============================================================================


class FTSErrorType(Enum):
    """FTSエラータイプの列挙型

    Values:
        PARSE_ERROR: クエリ解析エラー
        INDEX_ERROR: インデックス作成エラー
        QUERY_ERROR: クエリ実行エラー
        SYSTEM_ERROR: システムエラー
    """

    PARSE_ERROR = "parse_error"
    INDEX_ERROR = "index_error"
    QUERY_ERROR = "query_error"
    SYSTEM_ERROR = "system_error"


@dataclass(frozen=True)
class FTSError:
    """FTSエラーの不変データクラス

    Attributes:
        type: エラータイプ
        message: エラーメッセージ
        query: エラーが発生したクエリ（該当する場合）
        position: エラー発生位置（該当する場合）
    """

    type: FTSErrorType
    message: str
    query: str | None
    position: int | None


# calculate_cosine_similarity removed - VSS functionality deprecated


# cosine_distance_to_similarity removed - VSS functionality deprecated


# sort_results_by_similarity removed - VSS functionality deprecated


# select_top_k_results removed - VSS functionality deprecated


# find_semantically_similar_documents removed - VSS functionality deprecated


# ============================================================================
# Pure Functions - Domain logic
# ============================================================================


# validate_embedding_dimension removed - VSS functionality deprecated


# group_documents_by_topic_similarity removed - VSS functionality deprecated


# ============================================================================
# FTS (Full Text Search) Functions - Pure domain logic
# ============================================================================


def search_documents_by_keyword(
    documents: list[tuple[str, str, str]], keyword: str
) -> list[FTSSearchResult]:
    """
    単一キーワードでドキュメントを検索する純粋関数

    Args:
        documents: (id, title, content)のタプルリスト
        keyword: 検索キーワード

    Returns:
        キーワードに一致するドキュメントの検索結果
    """
    results = []
    keyword_lower = keyword.lower()

    for doc_id, title, content in documents:
        full_text = f"{title} {content}"
        if keyword_lower in full_text.lower():
            # ハイライトと位置情報を生成
            highlights = []
            positions = []

            # タイトルでの出現をチェック
            if keyword_lower in title.lower():
                highlights.append(title)
                positions.append((0, len(title)))

            # コンテンツでの出現をチェック
            if keyword_lower in content.lower():
                highlights.append(content)
                positions.append((len(title) + 1, len(title) + 1 + len(content)))

            result = FTSSearchResult(
                id=doc_id,
                content=full_text,
                score=1.0,  # 単純なキーワードマッチなので固定スコア
                highlights=tuple(highlights),
                position_info=tuple(positions),
            )
            results.append(result)

    return results


def search_documents_with_or_logic(
    documents: list[tuple[str, str, str]], keywords: list[str]
) -> list[FTSSearchResult]:
    """
    複数キーワードのOR検索を行う純粋関数

    Args:
        documents: (id, title, content)のタプルリスト
        keywords: 検索キーワードのリスト

    Returns:
        いずれかのキーワードに一致するドキュメントの検索結果
    """
    results = []
    keywords_lower = [k.lower() for k in keywords]
    seen_ids = set()

    for doc_id, title, content in documents:
        full_text = f"{title} {content}"
        full_text_lower = full_text.lower()

        matched = False
        for keyword in keywords_lower:
            if keyword in full_text_lower:
                matched = True
                break

        if matched and doc_id not in seen_ids:
            seen_ids.add(doc_id)
            result = FTSSearchResult(
                id=doc_id,
                content=full_text,
                score=1.0,
                highlights=(full_text,),
                position_info=((0, len(full_text)),),
            )
            results.append(result)

    return results


def calculate_bm25_score(
    doc_freq: int,
    doc_length: int,
    avg_doc_length: float,
    total_docs: int,
    docs_with_term: int,
    k1: float = 1.2,
    b: float = 0.75,
) -> float:
    """
    BM25スコアを計算する純粋関数

    Args:
        doc_freq: ドキュメント内の用語出現回数
        doc_length: ドキュメントの長さ（単語数）
        avg_doc_length: 全ドキュメントの平均長
        total_docs: 全ドキュメント数
        docs_with_term: 用語を含むドキュメント数
        k1: BM25パラメータ（デフォルト1.2）
        b: BM25パラメータ（デフォルト0.75）

    Returns:
        BM25スコア
    """
    # IDF計算 - 常に正の値を返すように調整
    idf = max(0, np.log((total_docs - docs_with_term + 0.5) / (docs_with_term + 0.5)))

    # 正規化された文書長
    norm_doc_length = doc_length / avg_doc_length if avg_doc_length > 0 else 1.0

    # BM25スコア計算
    score = idf * (doc_freq * (k1 + 1)) / (doc_freq + k1 * (1 - b + b * norm_doc_length))

    # 頻度が高い場合により高いスコアを保証するため、頻度ボーナスを追加
    # IDF が 0 の場合は、単純に頻度を使用
    if idf == 0:
        score = doc_freq / (1 + doc_length)

    return float(score)


def search_with_bm25_scoring(
    documents: list[tuple[str, str, str]], keyword: str
) -> list[FTSSearchResult]:
    """
    BM25スコアリングを使用して検索する純粋関数

    Args:
        documents: (id, title, content)のタプルリスト
        keyword: 検索キーワード

    Returns:
        BM25スコアでランク付けされた検索結果
    """
    keyword_lower = keyword.lower()
    results = []

    # ドキュメント統計を計算
    doc_lengths = []
    docs_with_term = 0

    for _, title, content in documents:
        full_text = f"{title} {content}"
        doc_lengths.append(len(full_text.split()))
        if keyword_lower in full_text.lower():
            docs_with_term += 1

    avg_doc_length = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 1.0
    total_docs = len(documents)

    # 各ドキュメントでBM25スコアを計算
    for i, (doc_id, title, content) in enumerate(documents):
        full_text = f"{title} {content}"
        full_text_lower = full_text.lower()

        if keyword_lower in full_text_lower:
            # 用語頻度をカウント - 単語境界を考慮
            words = full_text_lower.split()
            doc_freq = sum(1 for word in words if keyword_lower in word)
            doc_length = doc_lengths[i]

            # BM25スコアを計算
            score = calculate_bm25_score(
                doc_freq=doc_freq,
                doc_length=doc_length,
                avg_doc_length=avg_doc_length,
                total_docs=total_docs,
                docs_with_term=docs_with_term,
            )

            result = FTSSearchResult(
                id=doc_id,
                content=full_text,
                score=score,
                highlights=(full_text,),
                position_info=((0, len(full_text)),),
            )
            results.append(result)

    # スコアで降順ソート
    return sorted(results, key=lambda r: r.score, reverse=True)


def create_highlight_info(text: str, keyword: str) -> tuple[list[str], list[tuple[int, int]]]:
    """
    テキスト内のキーワード出現箇所のハイライト情報を生成する純粋関数

    Args:
        text: 検索対象テキスト
        keyword: ハイライトするキーワード

    Returns:
        (ハイライトテキストのリスト, 位置情報のリスト)のタプル
    """
    text_lower = text.lower()
    keyword_lower = keyword.lower()
    highlights = []
    positions = []

    start = 0
    while True:
        pos = text_lower.find(keyword_lower, start)
        if pos == -1:
            break

        # ハイライト部分を抽出
        highlight_start = max(0, pos - 20)
        highlight_end = min(len(text), pos + len(keyword) + 20)
        highlight = text[highlight_start:highlight_end]

        highlights.append(highlight)
        positions.append((pos, pos + len(keyword)))

        start = pos + 1

    return highlights, positions


def search_with_highlights(
    documents: list[tuple[str, str, str]], keyword: str
) -> list[FTSSearchResult]:
    """
    ハイライト情報付きで検索する純粋関数

    Args:
        documents: (id, title, content)のタプルリスト
        keyword: 検索キーワード

    Returns:
        ハイライト情報を含む検索結果
    """
    results = []

    for doc_id, title, content in documents:
        # タイトルでのハイライト
        title_highlights, title_positions = create_highlight_info(title, keyword)

        # コンテンツでのハイライト
        content_highlights, content_positions = create_highlight_info(content, keyword)

        if title_highlights or content_highlights:
            all_highlights = []
            all_positions = []

            # タイトルのハイライトを追加
            for highlight, (start, end) in zip(title_highlights, title_positions, strict=False):
                all_highlights.append(highlight)
                all_positions.append((start, end))

            # コンテンツのハイライトを追加（オフセット付き）
            title_offset = len(title) + 1  # スペース分を考慮
            for highlight, (start, end) in zip(content_highlights, content_positions, strict=False):
                all_highlights.append(highlight)
                all_positions.append((title_offset + start, title_offset + end))

            result = FTSSearchResult(
                id=doc_id,
                content=f"{title} {content}",
                score=len(all_highlights),  # 出現回数をスコアとする
                highlights=tuple(all_highlights),
                position_info=tuple(all_positions),
            )
            results.append(result)

    return results


def search_phrase(documents: list[tuple[str, str, str]], phrase: str) -> list[FTSSearchResult]:
    """
    フレーズ検索を行う純粋関数（完全一致）

    Args:
        documents: (id, title, content)のタプルリスト
        phrase: 検索フレーズ

    Returns:
        フレーズに完全一致するドキュメントの検索結果
    """
    results = []
    phrase_lower = phrase.lower()

    for doc_id, title, content in documents:
        full_text = f"{title} {content}"
        full_text_lower = full_text.lower()

        if phrase_lower in full_text_lower:
            # フレーズの位置を見つける
            positions = []
            start = 0
            while True:
                pos = full_text_lower.find(phrase_lower, start)
                if pos == -1:
                    break
                positions.append((pos, pos + len(phrase)))
                start = pos + 1

            if positions:
                result = FTSSearchResult(
                    id=doc_id,
                    content=full_text,
                    score=len(positions),  # 出現回数をスコアとする
                    highlights=(phrase,) * len(positions),
                    position_info=tuple(positions),
                )
                results.append(result)

    return results


def validate_conjunctive_results(
    documents: list[tuple[str, str, str]], keywords: list[str]
) -> list[FTSSearchResult]:
    """
    AND検索を行う純粋関数（すべてのキーワードを含む）

    Args:
        documents: (id, title, content)のタプルリスト
        keywords: 検索キーワードのリスト

    Returns:
        すべてのキーワードを含むドキュメントの検索結果
    """
    results = []
    keywords_lower = [k.lower() for k in keywords]

    for doc_id, title, content in documents:
        full_text = f"{title} {content}"
        full_text_lower = full_text.lower()

        # すべてのキーワードが含まれているかチェック
        all_found = all(keyword in full_text_lower for keyword in keywords_lower)

        if all_found:
            # 各キーワードの出現回数を合計してスコアとする
            total_occurrences = sum(full_text_lower.count(k) for k in keywords_lower)

            result = FTSSearchResult(
                id=doc_id,
                content=full_text,
                score=total_occurrences,
                highlights=(full_text,),
                position_info=((0, len(full_text)),),
            )
            results.append(result)

    return results


def boost_title_matches(
    documents: list[tuple[str, str, str]], keyword: str, title_boost: float = 2.0
) -> list[FTSSearchResult]:
    """
    タイトルマッチをブーストして検索する純粋関数

    Args:
        documents: (id, title, content)のタプルリスト
        keyword: 検索キーワード
        title_boost: タイトルマッチのブースト係数

    Returns:
        タイトルマッチをブーストした検索結果
    """
    results = []
    keyword_lower = keyword.lower()

    for doc_id, title, content in documents:
        title_lower = title.lower()
        content_lower = content.lower()

        title_count = title_lower.count(keyword_lower)
        content_count = content_lower.count(keyword_lower)

        if title_count > 0 or content_count > 0:
            # タイトルマッチにブーストを適用
            score = (title_count * title_boost) + content_count

            result = FTSSearchResult(
                id=doc_id,
                content=f"{title} {content}",
                score=score,
                highlights=(f"{title} {content}",),
                position_info=((0, len(title) + len(content) + 1),),
            )
            results.append(result)

    # スコアで降順ソート
    return sorted(results, key=lambda r: r.score, reverse=True)


def filter_by_section(
    documents: list[tuple[str, str, str]], keyword: str, section: str
) -> list[FTSSearchResult]:
    """
    特定セクション内でのみ検索する純粋関数

    Args:
        documents: (id, title, content)のタプルリスト
        keyword: 検索キーワード
        section: 検索対象セクション名

    Returns:
        指定セクション内でキーワードに一致する検索結果
    """
    results = []
    keyword_lower = keyword.lower()
    section_pattern = f"{section}:"

    for doc_id, title, content in documents:
        # セクションを含むコンテンツから該当セクションを抽出
        if section_pattern in content:
            # セクションの開始位置を見つける
            section_start = content.find(section_pattern)

            # 次のセクションの開始位置を見つける（セクションの終わり）
            next_section_markers = [
                "INTRODUCTION:",
                "REQUIREMENTS:",
                "APPENDIX:",
                "OVERVIEW:",
                "IMPLEMENTATION:",
                "TEST CASES:",
                "RESULTS:",
            ]
            section_end = len(content)

            for marker in next_section_markers:
                if (
                    marker != section_pattern
                    and marker in content[section_start + len(section_pattern) :]
                ):
                    pos = content.find(marker, section_start + len(section_pattern))
                    if pos < section_end:
                        section_end = pos

            # セクション内のテキストを抽出
            section_text = content[section_start:section_end]

            # セクション内でキーワードを検索
            if keyword_lower in section_text.lower():
                result = FTSSearchResult(
                    id=doc_id,
                    content=f"{title} {content}",
                    score=1.0,
                    highlights=(section_text,),
                    position_info=((section_start, section_end),),
                )
                results.append(result)

    return results
