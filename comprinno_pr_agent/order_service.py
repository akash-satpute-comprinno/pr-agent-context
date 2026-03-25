import sqlite3

def get_order(order_id):
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    # FIXED: parameterized query
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def delete_order(order_id):
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    # NEW BUG: SQL injection introduced
    cursor.execute("DELETE FROM orders WHERE id = " + str(order_id))
    conn.commit()
    # BUG: connection not closed on error path
    conn.close()

def get_all_orders():
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    # BUG: no pagination - returns all records
    cursor.execute("SELECT * FROM orders")
    return cursor.fetchall()
