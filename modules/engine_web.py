# Module for web-only configuration and basic routines (minimal dependencies)

import os # For environment variables
import base64 # For base64 encoding/decoding
from Crypto.Cipher import AES # For AES encryption/decryption
from Crypto.Util.Padding import pad, unpad # For padding in AES

# ========================================================
# Configuration data
# ========================================================

# AWS S3 storage settings
AWS_EXTERNAL_URL = os.getenv("AWS_EXTERNAL_URL").rstrip("/")

# WEB parameters
HTTP_PORT = int(os.getenv("HTTP_PORT", "80"))
HTTPS_PORT = int(os.getenv("HTTPS_PORT", "443"))
SSL_CERT_PATH = os.getenv("SSL_CERT_PATH")
SSL_KEY_PATH = os.getenv("SSL_KEY_PATH")
URL_BASE = os.getenv("URL_BASE")
URL_KEY = os.getenv("URL_KEY")

# ========================================================
# Routines defenitions
# ========================================================

# -------------------------------------------------------
# AES Encryption text for URL usage
def encrypt_for_url(text):
    cipher = AES.new(URL_KEY.encode(), AES.MODE_ECB)
    encrypted = cipher.encrypt(pad(text.encode(), AES.block_size))
    return base64.urlsafe_b64encode(encrypted).decode().rstrip('=')

# -------------------------------------------------------
# AES Decryption text from URL
def decrypt_from_url(encrypted):
    # Add padding if necessary
    padding = 4 - (len(encrypted) % 4)
    if padding != 4:
        encrypted += '=' * padding
    # Decrypt
    cipher = AES.new(URL_KEY.encode(), AES.MODE_ECB)
    text = unpad(cipher.decrypt(base64.urlsafe_b64decode(encrypted)), AES.block_size)
    return text.decode()
