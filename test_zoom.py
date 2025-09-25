#!/usr/bin/env python3
"""
Test script for the new zoom functions
"""
import sys
import os
import time

# Add src directory to path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from adb_utils import zoom_in, zoom_out, ensure_adb_connection

def test_zoom_functions():
    """Test the zoom in and zoom out functions"""
    print("Testing zoom functions...")

    try:
        # Ensure ADB connection is working
        print("Checking ADB connection...")
        ensure_adb_connection()
        print("ADB connection OK")

        # Test zoom out
        print("Testing zoom out (Ctrl+-)...")
        zoom_out()
        time.sleep(2)

        # Test zoom in
        print("Testing zoom in (Ctrl++)...")
        zoom_in()
        time.sleep(2)

        print("Zoom tests completed successfully!")

    except Exception as e:
        print(f"Zoom test failed: {e}")
        return False

    return True

if __name__ == "__main__":
    success = test_zoom_functions()
    if success:
        print("All tests passed!")
    else:
        print("Some tests failed!")
        sys.exit(1)