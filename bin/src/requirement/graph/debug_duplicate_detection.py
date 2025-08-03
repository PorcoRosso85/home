#!/usr/bin/env python3
"""Debug script to test duplicate detection and similarity calculation"""

import tempfile
import json
import sys
import os
import subprocess
from pathlib import Path

def run_command(command_dict, db_path):
    """Run a command through the requirement graph system"""
    env = os.environ.copy()
    env['RGL_DATABASE_PATH'] = db_path
    
    proc = subprocess.Popen(
        ['python', '-m', 'main'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        cwd=Path(__file__).parent
    )
    
    stdout, stderr = proc.communicate(json.dumps(command_dict))
    
    if stderr:
        print(f"STDERR: {stderr}")
    
    try:
        return json.loads(stdout.strip())
    except json.JSONDecodeError:
        print(f"Failed to decode JSON. Raw output: {stdout}")
        return {"error": "Failed to decode JSON response"}

def test_duplicate_detection():
    """Test duplicate detection behavior"""
    with tempfile.TemporaryDirectory() as db_dir:
        print(f"Using temporary database: {db_dir}")
        
        # Initialize schema
        print("\n1. Initializing schema...")
        schema_result = run_command({"type": "schema", "action": "apply"}, db_dir)
        print(f"Schema result: {json.dumps(schema_result, indent=2)}")
        
        # Create first requirement
        print("\n2. Creating first requirement...")
        req1_result = run_command({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "auth_001",
                "title": "ユーザー認証機能",
                "description": "安全なログイン機能を提供"
            }
        }, db_dir)
        print(f"First requirement result: {json.dumps(req1_result, indent=2)}")
        
        # Create similar requirement
        print("\n3. Creating similar requirement...")
        req2_result = run_command({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "auth_002",
                "title": "ユーザー認証システム",
                "description": "セキュアなログイン実装"
            }
        }, db_dir)
        print(f"Second requirement result: {json.dumps(req2_result, indent=2)}")
        
        # Check if warning exists and has score
        if "warning" in req2_result:
            warning = req2_result["warning"]
            print(f"\n4. Warning detected: {warning.get('type')}")
            if "duplicates" in warning:
                print(f"Number of duplicates: {len(warning['duplicates'])}")
                for dup in warning["duplicates"]:
                    print(f"  - ID: {dup.get('id')}, Score: {dup.get('score')}")
        else:
            print("\n4. No warning detected")
        
        # Test search directly
        print("\n5. Testing search functionality...")
        # Import within the function to handle module loading in subprocess
        try:
            # Add parent to path for imports
            sys.path.insert(0, str(Path(__file__).parent))
            from application.search_adapter import SearchAdapter, VSS_MODULES_AVAILABLE, FTS_MODULES_AVAILABLE
            
            print(f"VSS modules available: {VSS_MODULES_AVAILABLE}")
            print(f"FTS modules available: {FTS_MODULES_AVAILABLE}")
            
            # Create search adapter
            adapter = SearchAdapter(db_dir)
            print(f"Search adapter created. VSS available: {adapter.vss_available}, FTS available: {adapter.fts_available}")
            
            # Test search
            search_results = adapter.check_duplicates("ユーザー認証システム セキュアなログイン実装", k=5, threshold=0.5)
            print(f"\nSearch results: {json.dumps(search_results, indent=2)}")
        except Exception as e:
            print(f"Error testing search: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_duplicate_detection()