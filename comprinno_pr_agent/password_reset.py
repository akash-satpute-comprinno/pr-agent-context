import random
import logging
import sqlite3

logger = logging.getLogger(__name__)

def generate_reset_token(email):
    # BUG: weak token - predictable random
    token = str(random.randint(100000, 999999))
    logger.info(f"Generated reset token {token} for user {email}")  # BUG: logs sensitive data
    return token

def request_password_reset(email):
    # BUG: no email format validation
    # BUG: no rate limiting
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    token = generate_reset_token(email)
    # BUG: token stored with no expiry
    cursor.execute("INSERT INTO reset_tokens VALUES ('" + email + "', '" + token + "')")  # BUG: SQL injection
    conn.commit()
    conn.close()
    return token

def verify_reset_token(email, token):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    # BUG: no expiry check
    cursor.execute("SELECT * FROM reset_tokens WHERE email=? AND token=?", (email, token))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def reset_password(email, token, new_password):
    if not verify_reset_token(email, token):
        return False
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    # BUG: password stored as plain text
    cursor.execute("UPDATE users SET password=? WHERE email=?", (new_password, email))
    conn.commit()
    conn.close()
    logger.info(f"Password reset for {email}")
    return True
