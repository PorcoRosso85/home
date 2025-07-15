#!/usr/bin/env python3
"""Simple tests for FTS with mocked connection"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_mock import MockConnection
from main import create_text_search
from fts_types import IndexSuccess, SearchSuccess


def test_basic_functionality():
    """Test basic FTS functionality with mocked connection."""
    # Create mock connection
    conn = MockConnection()

    # Create text search operations
    search_ops = create_text_search(conn)

    # Test 1: Create index
    print("Test 1: Create index...")
    result = search_ops["create_index"](["title", "content"])
    assert result["ok"] is True
    assert "title" in result["message"]
    print("✓ Create index passed")

    # Test 2: Search with empty query
    print("\nTest 2: Empty query validation...")
    result = search_ops["search"]("", False)
    assert result["ok"] is False
    assert "empty query" in result["error"].lower()
    print("✓ Empty query validation passed")

    # Test 3: Search with results
    print("\nTest 3: Search with results...")
    # Set mock results
    conn.set_results([[[{"id": "1", "title": "Test Doc", "content": "Test content"}, 5.0]]])
    result = search_ops["search"]("test", False)
    assert result["ok"] is True
    assert len(result["results"]) == 1
    assert result["results"][0]["title"] == "Test Doc"
    print("✓ Search with results passed")

    # Test 4: Get indexed fields
    print("\nTest 4: Get indexed fields...")
    result = search_ops["get_indexed_fields"]()
    assert result["ok"] is True
    assert result["fields"] == ["title", "content"]
    print("✓ Get indexed fields passed")

    # Test 5: Batch index markdown files
    print("\nTest 5: Batch index markdown files...")
    result = search_ops["batch_index_markdown_files"]("/poc/search")
    assert result["ok"] is True
    assert result["indexed_count"] >= 0
    print("✓ Batch index passed")

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    test_basic_functionality()
