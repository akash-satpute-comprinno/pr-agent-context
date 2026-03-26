# app_config.py - Application security configuration
import os
from datetime import timedelta

# FIXED: Raise error if secrets not set in environment
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable is required")

# FIXED: JWT tokens expire after 24 hours
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

# BUG: stray text still present
Hi hello

def get_app_config():
    return {
        "SECRET_KEY": SECRET_KEY,
        "JWT_SECRET_KEY": JWT_SECRET_KEY,
        "JWT_ACCESS_TOKEN_EXPIRES": JWT_ACCESS_TOKEN_EXPIRES,
    }
