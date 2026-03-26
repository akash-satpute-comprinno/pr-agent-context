import json

# Constant instead of magic number
TAX_RATE = 0.15


def calculate_total(items):
    """Calculate total price including tax."""
    total = sum(item['price'] for item in items)
    return total * (1 + TAX_RATE)


# DRY fix: reuse calculate_total instead of duplicating logic
def calculate_order_total(orders):
    """Calculate order total — delegates to calculate_total."""
    return calculate_total(orders)


def process_data(data):
    """Filter valid items — simplified nested logic."""
    result = []
    for item in data:
        if not item:
            continue
        name = item.get('name', '').strip()
        price = item.get('price', 0)
        if name and 0 < price < 1000:
            result.append(item)
    return result


class DataLoader:
    """Single responsibility: load and save data."""
    def __init__(self):
        self.data = []

    def load(self, filepath: str):
        with open(filepath, 'r') as f:
            self.data = json.load(f)

    def save(self, filepath: str):
        with open(filepath, 'w') as f:
            json.dump(self.data, f)


class DataValidator:
    """Single responsibility: validate data."""
    def validate(self, data: list) -> bool:
        return all(
            isinstance(item, dict) and 'name' in item and 'price' in item
            for item in data
        )


class ReportGenerator:
    """Single responsibility: generate reports."""
    def generate(self, data: list) -> str:
        return json.dumps(data, indent=2)
