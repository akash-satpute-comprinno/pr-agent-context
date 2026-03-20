# Sample Python file with intentional code issues for testing

def calculate_total(items):
    # Magic number - should be a constant
    tax_rate = 0.15
    total = 0
    for item in items:
        total += item['price']
    total = total + (total * tax_rate)
    return total

def calculate_order_total(orders):
    # DRY Violation - duplicate code from above
    tax_rate = 0.15
    total = 0
    for order in orders:
        total += order['price']
    total = total + (total * tax_rate)
    return total

# Dead code - unused function
def old_calculation(x, y):
    return x + y

# Long method - exceeds 50 lines
def process_data(data):
    result = []
    for i in range(len(data)):
        item = data[i]
        if item:
            if 'name' in item:
                if item['name']:
                    if len(item['name']) > 0:
                        if item['name'].strip():
                            # Nested complexity
                            if 'price' in item:
                                if item['price'] > 0:
                                    if item['price'] < 1000:
                                        result.append(item)
                                    else:
                                        print("Price too high")
                                else:
                                    print("Invalid price")
                            else:
                                print("No price")
                        else:
                            print("Empty name")
                    else:
                        print("Name too short")
                else:
                    print("Name is None")
            else:
                print("No name field")
        else:
            print("Item is None")
    return result

# God class - too many responsibilities
class DataManager:
    def __init__(self):
        self.data = []
    
    def load_data(self):
        pass
    
    def save_data(self):
        pass
    
    def validate_data(self):
        pass
    
    def transform_data(self):
        pass
    
    def export_to_csv(self):
        pass
    
    def export_to_json(self):
        pass
    
    def export_to_xml(self):
        pass
    
    def send_email(self):
        pass
    
    def generate_report(self):
        pass
    
    def backup_data(self):
        pass
    
    def restore_data(self):
        pass
    
    def compress_data(self):
        pass
    
    def decompress_data(self):
        pass
    
    def encrypt_data(self):
        pass
    
    def decrypt_data(self):
        pass

# Unused import would be here
import json
import sys
import os
# sys and os are not used - dead imports
