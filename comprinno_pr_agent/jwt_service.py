import jwt
import datetime

SECRET_KEY = "mysecretkey123"  # hardcoded secret

def generate_token(user_id):
    # BUG: token never expires
    payload = {
        "user_id": user_id,
        "role": "admin"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token):
    # BUG: no exception handling
    decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return decoded

def get_user_data(user_id):
    import sqlite3
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    # BUG: SQL injection
    cursor.execute("SELECT * FROM users WHERE id = " + str(user_id))
    return cursor.fetchall()
