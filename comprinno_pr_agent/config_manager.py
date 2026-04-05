import os
from typing import Optional

class ConfigManager:
    """Secure configuration manager - loads all values from environment"""

    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        self.api_key = os.getenv("PAYMENT_API_KEY")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return os.getenv(key, default)

    def require(self, key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required config {key} is not set")
        return value
