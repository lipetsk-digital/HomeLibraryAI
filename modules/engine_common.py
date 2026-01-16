# Module for configuraion data, environment variables, and basic routines

import os # For environment variables
import logging # For logging

# ========================================================
# Configuration data
# ========================================================

# PostgreSQL connection settings
POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "database": os.getenv("POSTGRES_DATABASE"),
    "user": os.getenv("POSTGRES_USERNAME"),
    "password": os.getenv("POSTGRES_PASSWORD")
}

# ========================================================
# Environment variables
# ========================================================

pool = None  # Placeholder for database connection pool

# ========================================================
# Start section
# ========================================================

# Logging configuration
logging.basicConfig(level=logging.INFO)
