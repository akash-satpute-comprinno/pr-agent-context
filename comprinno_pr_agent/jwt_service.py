import jwt
import datetime
import os
import sqlite3

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret")

def generate_token(user_id):
    payload = {
        "user_id": user_id,
        "role": "admin",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token):
    # FIXED: added exception handling
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")

def get_user_data(user_id):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    # FIXED: parameterized query
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchall()
    # BUG: connection never closed — resource leak introduced

def delete_user(user_id):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    # BUG: new SQL injection introduced while fixing
    cursor.execute("DELETE FROM users WHERE id = " + str(user_id))
    conn.commit()
    conn.close()
