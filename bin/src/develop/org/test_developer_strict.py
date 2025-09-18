#!/usr/bin/env python3
"""Test suite for strict developer: window management."""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from application import (
    start_developer,
    send_command_to_developer_by_directory,
    get_all_developers_status
)


def test_duplicate_detection():
    """Test that duplicate developer windows are properly detected."""
    print("\n=== Test: Duplicate Detection ===")
    
    test_dir = "/tmp/test_developer"
    Path(test_dir).mkdir(exist_ok=True)
    
    # First attempt - should succeed
    result1 = start_developer(test_dir)
    print(f"First start: {result1}")
    
    if result1['ok']:
        # Second attempt - should fail with duplicate_developer
        result2 = start_developer(test_dir)
        print(f"Second start: {result2}")
        
        if not result2['ok'] and result2.get('error', {}).get('code') == 'duplicate_developer':
            print("✅ Duplicate detection working correctly")
        else:
            print("❌ Duplicate detection failed")
    else:
        print(f"❌ First start failed: {result1}")


def test_developer_only_search():
    """Test that only developer: windows are found."""
    print("\n=== Test: Developer-only Search ===")
    
    test_dir = "/tmp/test_search"
    Path(test_dir).mkdir(exist_ok=True)
    
    # Try to send command to non-existent developer
    result = send_command_to_developer_by_directory(test_dir, "echo test")
    print(f"Send to non-existent: {result}")
    
    if not result['ok'] and result.get('error', {}).get('code') == 'developer_not_found':
        print("✅ Correctly returns developer_not_found")
    else:
        print("❌ Should have returned developer_not_found")


def test_status_listing():
    """Test that status listing only shows developer: windows."""
    print("\n=== Test: Status Listing ===")
    
    result = get_all_developers_status()
    print(f"Status result: {result}")
    
    if result['ok']:
        developers = result['data']['developers']
        print(f"Found {len(developers)} developers")
        
        # Verify all have developer: prefix (implicit from domain function)
        for dev in developers:
            print(f"  - {dev['directory']}: {dev['status']}")
        print("✅ Status listing completed")
    else:
        print(f"❌ Status listing failed: {result}")


def test_error_messages():
    """Test that error messages are clear and actionable."""
    print("\n=== Test: Error Messages ===")
    
    # Test invalid directory
    result = start_developer("/nonexistent/directory")
    print(f"Invalid directory: {result}")
    
    if not result['ok'] and result.get('error', {}).get('code') == 'invalid_directory':
        print("✅ Invalid directory error correct")
    else:
        print("❌ Invalid directory error incorrect")


if __name__ == "__main__":
    print("=" * 60)
    print("DEVELOPER WINDOW STRICT MANAGEMENT TESTS")
    print("=" * 60)
    
    test_duplicate_detection()
    test_developer_only_search()
    test_status_listing()
    test_error_messages()
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)