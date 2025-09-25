#!/usr/bin/env python3
"""
Test script for dynamic threshold functionality in image_utils.py
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from image_utils import (
    find_trophy_coordinates,
    find_coin_coordinates,
    find_elixir_coordinates,
    load_thresholds_from_config,
    save_thresholds_to_config,
    load_best_match_threshold
)

def test_dynamic_thresholds():
    """Test the improved dynamic threshold functionality"""
    print("Testing Improved Dynamic Threshold Functionality")
    print("=" * 60)

    # Test loading thresholds from config
    print("\n1. Loading thresholds from config:")
    thresholds = load_thresholds_from_config()
    print(f"Current thresholds: {thresholds}")

    # Test trophy detection with dynamic threshold
    print("\n2. Testing trophy detection with improved dynamic threshold:")
    print("   This will use binary search to find optimal threshold")
    trophy_coords = find_trophy_coordinates(use_dynamic=True)
    if trophy_coords:
        print(f"   ✓ Trophy coordinates found: {trophy_coords}")
    else:
        print("   ✗ Trophy coordinates not found")

    # Test coin detection with dynamic threshold
    print("\n3. Testing coin detection with improved dynamic threshold:")
    print("   This will intelligently adjust threshold based on match count")
    coin_coords = find_coin_coordinates(use_dynamic=True)
    if coin_coords:
        print(f"   ✓ Coin coordinates found: {coin_coords}")
    else:
        print("   ✗ Coin coordinates not found")

    # Test elixir detection with dynamic threshold
    print("\n4. Testing elixir detection with improved dynamic threshold:")
    print("   Uses smaller steps (0.05) and handles large match count differences")
    elixir_coords = find_elixir_coordinates(use_dynamic=True)
    if elixir_coords:
        print(f"   ✓ Elixir coordinates found: {elixir_coords}")
    else:
        print("   ✗ Elixir coordinates not found")

    # Show final thresholds
    print("\n5. Final thresholds after improved dynamic adjustment:")
    final_thresholds = load_thresholds_from_config()
    print(f"Updated thresholds: {final_thresholds}")

    # Show the differences
    print("\n6. Threshold changes:")
    for key in thresholds:
        old_val = thresholds[key]
        new_val = final_thresholds.get(key, old_val)
        change = new_val - old_val
        if change != 0:
            print(f"   {key}: {old_val:.3f} → {new_val:.3f} (change: {change:+.3f})")
        else:
            print(f"   {key}: {old_val:.3f} (no change)")

    # Show best match thresholds
    print("\n7. Best match thresholds (single-digit matches closest to 0):")
    for function_name in ["trophy", "coin", "elixir", "general"]:
        best_match_info = load_best_match_threshold(function_name)
        if best_match_info:
            threshold = best_match_info["threshold"]
            match_count = best_match_info["match_count"]
            confidence = best_match_info["confidence"]
            print(f"   ★ {function_name}: {threshold:.3f} ({match_count} matches, confidence: {confidence:.3f})")
        else:
            print(f"   - {function_name}: No best match threshold found yet")

    print("\n" + "=" * 60)
    print("Improved test completed!")

def test_fixed_thresholds():
    """Test the traditional fixed threshold functionality"""
    print("\nTesting Fixed Threshold Functionality (for comparison)")
    print("=" * 50)

    # Test trophy detection with fixed threshold
    print("\n1. Testing trophy detection with fixed threshold (0.6):")
    trophy_coords = find_trophy_coordinates(threshold=0.6, use_dynamic=False)
    if trophy_coords:
        print(f"Trophy coordinates found: {trophy_coords}")
    else:
        print("Trophy coordinates not found")

    # Test coin detection with fixed threshold
    print("\n2. Testing coin detection with fixed threshold (0.6):")
    coin_coords = find_coin_coordinates(threshold=0.6, use_dynamic=False)
    if coin_coords:
        print(f"Coin coordinates found: {coin_coords}")
    else:
        print("Coin coordinates not found")

    # Test elixir detection with fixed threshold
    print("\n3. Testing elixir detection with fixed threshold (0.6):")
    elixir_coords = find_elixir_coordinates(threshold=0.6, use_dynamic=False)
    if elixir_coords:
        print(f"Elixir coordinates found: {elixir_coords}")
    else:
        print("Elixir coordinates not found")

def show_best_match_summary():
    """Show summary of all best match thresholds"""
    print("\nBest Match Threshold Summary")
    print("=" * 40)

    functions = ["trophy", "coin", "elixir", "general"]
    found_any = False

    for function_name in functions:
        best_match_info = load_best_match_threshold(function_name)
        if best_match_info:
            found_any = True
            threshold = best_match_info["threshold"]
            match_count = best_match_info["match_count"]
            confidence = best_match_info["confidence"]
            timestamp = best_match_info.get("timestamp", 0)

            from datetime import datetime
            time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S") if timestamp else "Unknown"

            print(f"★ {function_name.upper()}")
            print(f"   Threshold: {threshold:.3f}")
            print(f"   Matches: {match_count} (single-digit, closest to 0)")
            print(f"   Confidence: {confidence:.3f}")
            print(f"   Found: {time_str}")
            print()

    if not found_any:
        print("No best match thresholds saved yet.")
        print("Run the dynamic threshold test to find optimal values!")

    print("=" * 40)

if __name__ == "__main__":
    print("Dynamic Threshold Template Matching Test")
    print("This script tests the improved dynamic threshold functionality")
    print("Make sure you have a 'trophy_screen.png' file in the current directory")
    print("and template files in the 'src/templates/' directory")

    choice = input("\nChoose test type:\n1. Dynamic threshold test\n2. Fixed threshold test\n3. Both tests\n4. Show best match summary\nEnter choice (1/2/3/4): ")

    if choice == "1":
        test_dynamic_thresholds()
    elif choice == "2":
        test_fixed_thresholds()
    elif choice == "3":
        test_dynamic_thresholds()
        test_fixed_thresholds()
    elif choice == "4":
        show_best_match_summary()
    else:
        print("Invalid choice. Running dynamic threshold test by default.")
        test_dynamic_thresholds()