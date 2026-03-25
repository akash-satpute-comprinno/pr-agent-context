import jwt
import datetime
import os
import sqlite3

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
    # FIXED: exception handling added
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")

def get_user_data(user_id):
    # FIXED: parameterized query + connection closed via context manager
    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchall()

def delete_user(user_id):
    # FIXED: parameterized query + connection closed via context manager
    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
