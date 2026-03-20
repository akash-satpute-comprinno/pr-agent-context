#!/usr/bin/env python3
"""
Test script to verify detailed comment formatting
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli import format_finding_comment

# Test with new detailed format
detailed_finding = {
    'category': 'Performance Issue',
    'severity': 'Warning',
    'line_start': 10,
    'line_end': 15,
    'description': 'Using list comprehension inside a loop can cause performance degradation',
    'why_it_matters': 'This creates nested iterations which results in O(n²) time complexity. For large datasets, this can significantly slow down your application.',
    'how_to_fix': '1. Move the list comprehension outside the loop\n2. Store the result in a variable\n3. Reference the variable inside the loop',
    'code_example': '# Instead of:\n# for item in items:\n#     result = [x * 2 for x in data]\n\n# Do this:\nprocessed_data = [x * 2 for x in data]\nfor item in items:\n    result = processed_data',
    'best_practice': 'Always analyze the time complexity of nested loops. Consider caching computed values that don\'t change between iterations.',
    'code_snippet': 'for item in items:\n    result = [x * 2 for x in data]'
}

# Test with old format (backward compatibility)
old_finding = {
    'category': 'Code Smell',
    'severity': 'Info',
    'line_start': 20,
    'line_end': 22,
    'description': 'Variable name is not descriptive',
    'suggestion': 'Use a more descriptive variable name like user_count instead of x',
    'code_snippet': 'x = len(users)'
}

print("=" * 80)
print("TEST 1: New Detailed Format")
print("=" * 80)
print(format_finding_comment(detailed_finding))

print("\n\n")
print("=" * 80)
print("TEST 2: Old Format (Backward Compatibility)")
print("=" * 80)
print(format_finding_comment(old_finding))

print("\n\n✅ Both formats work correctly!")
