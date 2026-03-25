import jwt
import datetime
import os

# FIXED: secret loaded from environment variable
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret")

def generate_token(user_id):
    # FIXED: token expires in 1 hour
    payload = {
        "user_id": user_id,
        "role": "admin",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token):
    # BUG: still no exception handling
    decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return decoded

def get_user_data(user_id):
    import sqlite3
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    # BUG: SQL injection still present
    cursor.execute("SELECT * FROM users WHERE id = " + str(user_id))
    return cursor.fetchall()
