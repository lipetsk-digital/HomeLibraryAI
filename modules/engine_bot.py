# Module for configuraion data, environment variables, and basic routines

import os # For environment variables

# ========================================================
# Configuration data
# ========================================================

# AWS S3 storage settings
AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

# VSEGPT API key
GPT_URL = os.getenv("GPT_URL")
GPT_API_TOKEN = os.getenv("GPT_API_TOKEN")
GPT_MODEL = os.getenv("GPT_MODEL")

# Miscellaneous constants
CountOfRecentBooks = 5
MaxBytesInCategoryName = 60 # 64 - len("cat")
MaxCharsInMessage = 4096
MaxButtonsInMessage = 60 # 80+ buttons got REPLY_MARKUP_TOO_LONG error from Telegram

