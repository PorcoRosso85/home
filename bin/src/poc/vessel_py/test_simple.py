#!/usr/bin/env python3
"""最小限のテスト"""
import subprocess


def test_vessel_simple_print():
    """Test that vessel can execute a simple print statement"""
    result = subprocess.run(
        ['python3', 'vessel.py'],
        input='print(5)',
        capture_output=True,
        text=True
    )
    
    assert result.stdout.strip() == '5'
    assert result.returncode == 0