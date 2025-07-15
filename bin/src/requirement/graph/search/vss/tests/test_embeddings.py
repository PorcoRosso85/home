#!/usr/bin/env python3
"""埋め込みモデル層のテスト - RED段階"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pytest
from vss.infrastructure import create_embedding_model
from vss.domain import EmbeddingRequest, EmbeddingType


def test_埋め込みモデルの初期化():
    """Ruri v3モデルが正しく初期化されること"""
    model = create_embedding_model("ruri-v3-30m")
    assert model.model_name == "cl-nagoya/ruri-v3-30m"
    assert model.dimension == 256


def test_クエリ埋め込みの生成():
    """検索クエリに適切なプレフィックスが付与されること"""
    model = create_embedding_model("ruri-v3-30m")
    request = EmbeddingRequest(
        text="瑠璃色とは",
        embedding_type=EmbeddingType.QUERY
    )
    result = model.encode(request)
    assert result.dimension == 256
    assert len(result.embeddings) == 256


def test_ドキュメント埋め込みの生成():
    """ドキュメントに適切なプレフィックスが付与されること"""
    model = create_embedding_model("ruri-v3-30m")
    request = EmbeddingRequest(
        text="瑠璃色は美しい青色です",
        embedding_type=EmbeddingType.DOCUMENT
    )
    result = model.encode(request)
    assert result.dimension == 256
    assert len(result.embeddings) == 256


def test_バッチ埋め込みの生成():
    """複数テキストの一括埋め込みが動作すること"""
    model = create_embedding_model("ruri-v3-30m")
    requests = [
        EmbeddingRequest(text="テキスト1", embedding_type=EmbeddingType.DOCUMENT),
        EmbeddingRequest(text="テキスト2", embedding_type=EmbeddingType.DOCUMENT),
    ]
    results = model.encode_batch(requests)
    assert len(results) == 2
    assert all(r.dimension == 256 for r in results)