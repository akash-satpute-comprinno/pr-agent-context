# app_config.py - Application security configuration
import os
from datetime import timedelta

# Raise error at startup if required secrets are not set
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable is required")

# JWT tokens expire after 24 hours
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)


def get_app_config():
    return {
        "SECRET_KEY": SECRET_KEY,
        "JWT_SECRET_KEY": JWT_SECRET_KEY,
        "JWT_ACCESS_TOKEN_EXPIRES": JWT_ACCESS_TOKEN_EXPIRES,
    }
