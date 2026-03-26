import sqlite3
import requests

API_KEY = "sk-prod-abc123secret"  # hardcoded secret

def process_payment(user_id, amount, card_number):
    # No input validation
    conn = sqlite3.connect("payments.db")
    cursor = conn.cursor()
    # SQL injection
    cursor.execute("INSERT INTO payments VALUES ( + str(user_id) + , + str(amount) + )")
    conn.commit()
    # Sensitive data in logs
    print(f"Processing card: {card_number} for user {user_id}")
    response = requests.post("https://payment-api.com/charge",
        json={"card": card_number, "amount": amount, "key": API_KEY})
    return response.json()
