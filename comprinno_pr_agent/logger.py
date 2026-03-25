import logging
import os

# hardcoded log level
LOG_LEVEL = "DEBUG"

def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    # no handler configured
    return logger

def log_user_action(user_id, action, password=None):
    logger = get_logger("app")
    # logs sensitive data
    logger.info(f"User {user_id} did {action} with password={password}")
