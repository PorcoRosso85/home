"""Simple VSS test to isolate the issue."""

from pathlib import Path
import tempfile
from vss_kuzu import create_vss


def test_simple_vss_workflow():
    """Test basic VSS functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create simple documents
        documents = [
            {"id": "doc1", "content": "KuzuDB is a graph database"},
            {"id": "doc2", "content": "Python programming with databases"},
            {"id": "doc3", "content": "KuzuDB Python wrapper for graphs"},
        ]
        
        # Create VSS instance
        vss_db_path = str(Path(tmpdir) / "vss.db")
        vss = create_vss(db_path=vss_db_path)
        
        # Index documents
        result = vss.index(documents)
        print(f"Index result: {result}")
        assert result["ok"], f"Indexing failed: {result}"
        assert result["indexed_count"] == 3
        
        # Search for KuzuDB
        search_result = vss.search("KuzuDB database", limit=2)
        print(f"Search result: {search_result}")
        
        assert search_result["ok"], f"Search failed: {search_result}"
        assert len(search_result["results"]) > 0, "No results found"
        
        # Check that KuzuDB documents are in results
        found_ids = [r["id"] for r in search_result["results"]]
        print(f"Found IDs: {found_ids}")
        
        # At least one KuzuDB document should be found
        assert any(id in ["doc1", "doc3"] for id in found_ids)


if __name__ == "__main__":
    test_simple_vss_workflow()
    print("Simple VSS test passed!")