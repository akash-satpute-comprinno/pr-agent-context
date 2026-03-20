# Code Analysis Report

**File:** `tests/sample_code.py`  
**Generated:** 2026-03-04 06:49:56  
**Analyzer:** Deep Code Analysis Agent (AAS-3)

---

## Summary

| Severity | Count |
|----------|-------|
| 🔴 Critical | 1 |
| 🟡 Warning | 5 |
| 🔵 Info | 2 |
| **Total** | **8** |

---

## Findings

### 1. 🔴 God Class

**Severity:** Critical  
**Location:** Lines 72-211

**Description:**  
Class DataManager has too many responsibilities.

**Suggestion:**  
Break down the class into smaller classes with single responsibilities.

**Code Snippet:**
```python
class DataManager:\n    def __init__(self):\n        self.data = []\n    def load_data(self):\n        pass\n    def save_data(self):\n        pass\n    def validate_data(self):\n        pass\n    def transform_data(self):\n        pass\n    def export_to_csv(self):\n        pass\n    def export_to_json(self):\n        pass\n    def export_to_xml(self):\n        pass\n    def send_email(self):\n        pass\n    def generate_report(self):\n        pass\n    def backup_data(self):\n        pass\n    def restore_data(self):\n        pass\n    def compress_data(self):\n        pass\n    def decompress_data(self):\n        pass\n    def encrypt_data(self):\n        pass\n    def decrypt_data(self):\n        pass
```

---

### 2. 🟡 DRY Violation

**Severity:** Warning  
**Location:** Lines 3-12

**Description:**  
Duplicate code for calculating total with tax.

**Suggestion:**  
Extract common logic into a separate function.

**Code Snippet:**
```python
def calculate_total(items):\n    tax_rate = 0.15\n    total = 0\n    for item in items:\n        total += item['price']\n    total = total + (total * tax_rate)\n    return total
```

---

### 3. 🟡 DRY Violation

**Severity:** Warning  
**Location:** Lines 14-23

**Description:**  
Duplicate code for calculating order total with tax.

**Suggestion:**  
Use the same function as in calculate_total.

**Code Snippet:**
```python
def calculate_order_total(orders):\n    tax_rate = 0.15\n    total = 0\n    for order in orders:\n        total += order['price']\n    total = total + (total * tax_rate)\n    return total
```

---

### 4. 🟡 Long Method

**Severity:** Warning  
**Location:** Lines 31-70

**Description:**  
Method process_data exceeds 50 lines.

**Suggestion:**  
Refactor the method to break it down into smaller functions.

**Code Snippet:**
```python
def process_data(data):\n    result = []\n    for i in range(len(data):\n        item = data[i]\n        if item:\n            if 'name' in item:\n                if item['name']:\n                    if len(item['name']) > 0:\n                        if item['name'].strip():\n                            if 'price' in item:\n                                if item['price'] > 0:\n                                    if item['price'] < 1000:\n                                        result.append(item)\n                                    else:\n                                        print("Price too high")\n                                else:\n                                    print("Invalid price")\n                            else:\n                                print("No price")\n                        else:\n                            print("Empty name")\n                    else:\n                        print("Name too short")\n                else:\n                    print("Name is None")\n            else:\n                print("No name field")\n        else:\n            print("Item is None")\n    return result
```

---

### 5. 🟡 Magic Number

**Severity:** Warning  
**Location:** Lines 3-4

**Description:**  
Hardcoded tax rate without a constant.

**Suggestion:**  
Define tax rate as a constant.

**Code Snippet:**
```python
tax_rate = 0.15
```

---

### 6. 🟡 High Complexity

**Severity:** Warning  
**Location:** Lines 31-70

**Description:**  
Method process_data has overly complex logic.

**Suggestion:**  
Simplify the logic by breaking it into smaller functions.

**Code Snippet:**
```python
def process_data(data):\n    result = []\n    for i in range(len(data):\n        item = data[i]\n        if item:\n            if 'name' in item:\n                if item['name']:\n                    if len(item['name']) > 0:\n                        if item['name'].strip():\n                            if 'price' in item:\n                                if item['price'] > 0:\n                                    if item['price'] < 1000:\n                                        result.append(item)\n                                    else:\n                                        print("Price too high")\n                                else:\n                                    print("Invalid price")\n                            else:\n                                print("No price")\n                        else:\n                            print("Empty name")\n                    else:\n                        print("Name too short")\n                else:\n                    print("Name is None")\n            else:\n                print("No name field")\n        else:\n            print("Item is None")\n    return result
```

---

### 7. 🔵 Dead Code

**Severity:** Info  
**Location:** Lines 25-29

**Description:**  
Unused function old_calculation.

**Suggestion:**  
Remove the function if it's not needed.

**Code Snippet:**
```python
def old_calculation(x, y):\n    return x + y
```

---

### 8. 🔵 Dead Code

**Severity:** Info  
**Location:** Lines 213-221

**Description:**  
Unused imports sys and os.

**Suggestion:**  
Remove unused imports.

**Code Snippet:**
```python
import json\nimport sys\nimport os
```

---

## Recommendations

1. Address **Critical** issues immediately before merging
2. Review **Warning** issues and plan fixes
3. Consider **Info** items for code quality improvements

---

*Generated by Deep Code Analysis Agent using AWS Bedrock Nova*
