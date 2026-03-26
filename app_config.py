# app_config.py - Application security configuration
import os
from datetime import timedelta

# BUG: Weak fallback secrets - will be used if env vars not set
SECRET_KEY = os.getenv("SECRET_KEY", "medai_secret_key_2024")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "medai_jwt_secret_2024")

# BUG: JWT tokens never expire
JWT_ACCESS_TOKEN_EXPIRES = False

Hi hello  # BUG: stray text - will cause runtime error

def get_app_config():
    return {
        "SECRET_KEY": SECRET_KEY,
        "JWT_SECRET_KEY": JWT_SECRET_KEY,
        "JWT_ACCESS_TOKEN_EXPIRES": JWT_ACCESS_TOKEN_EXPIRES,
    }
