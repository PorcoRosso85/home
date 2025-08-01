"""Basic test to verify Pyright is working correctly."""

import tempfile
import subprocess
import json
from pathlib import Path


def test_pyright_basic():
    """Test that Pyright can detect type errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple Python file with a type error
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("""
# This should create a type error
x: int = "this is a string"

def add(a: int, b: int) -> int:
    return a + b

# This should also create a type error
result = add("1", "2")
""")
        
        # Create pyrightconfig.json to ensure Pyright processes the file
        config_file = Path(tmpdir) / "pyrightconfig.json"
        config_file.write_text(json.dumps({
            "include": ["**/*.py"],
            "pythonVersion": "3.12",
            "typeCheckingMode": "basic"
        }))
        
        # Run Pyright
        print(f"Running Pyright in {tmpdir}")
        result = subprocess.run(
            ["pyright", "--outputjson"],
            cwd=tmpdir,
            capture_output=True,
            text=True
        )
        
        print(f"Return code: {result.returncode}")
        print(f"Stdout length: {len(result.stdout)}")
        
        # Parse output
        try:
            output = json.loads(result.stdout)
            diagnostics = output.get("diagnostics", [])
            print(f"Found {len(diagnostics)} diagnostics")
            
            for diag in diagnostics[:3]:  # Show first 3
                print(f"- {diag.get('severity')}: {diag.get('message')[:60]}...")
                
            # We expect at least 2 type errors
            assert len(diagnostics) >= 2, f"Expected at least 2 diagnostics, got {len(diagnostics)}"
            print("\n✅ Pyright is working correctly!")
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            print(f"Output: {result.stdout[:200]}...")
            raise


if __name__ == "__main__":
    test_pyright_basic()