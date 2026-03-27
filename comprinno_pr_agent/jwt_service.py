import jwt
import datetime
import os
import sqlite3

# Load secret from env — raise error if not set
SECRET_KEY = os.environ["JWT_SECRET_KEY"]

def generate_token(user_id: str, role: str) -> str:
    """Generate JWT token with expiry. Role must be passed explicitly."""
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> dict:
    """Verify JWT token with specific exception handling."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired — please log in again")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {e}")

def get_user_data(user_id: int) -> list:
    """Fetch user data using parameterized query with proper resource cleanup."""
    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchall()

def delete_user(user_id: int) -> None:
    """Delete user after verifying existence."""
    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
        if cursor.fetchone() is None:
            raise ValueError(f"User {user_id} does not exist")
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
