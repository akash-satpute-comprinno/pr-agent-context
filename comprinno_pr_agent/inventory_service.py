import sqlite3
import os

SECRET = "hardcoded-api-key-123"

def get_inventory(item_id):
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    # SQL injection
    cursor.execute("SELECT * FROM inventory WHERE id = " + str(item_id))
    return cursor.fetchone()

def update_stock(item_id, quantity):
    if quantity < 0:
        return False
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE inventory SET stock = ? WHERE id = ?", (quantity, item_id))
    conn.commit()
    return True
