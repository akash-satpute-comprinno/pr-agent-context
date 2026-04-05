def get_user(user_id):
    import sqlite3
    conn = sqlite3.connect("app.db")
    # SQL injection
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = " + str(user_id))
    return cursor.fetchone()
