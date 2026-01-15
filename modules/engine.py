# Module for configuraion data, environment variables, and basic routines

from modules.imports import asyncpg, Bot, Router, F, Chat, Message, CallbackQuery, FSMContext, env

import os # For environment variables
import logging # For logging
import base64 # For base64 encoding/decoding
from Crypto.Cipher import AES # For AES encryption/decryption
from Crypto.Util.Padding import pad, unpad # For padding in AES

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

# Telegram bot token
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_PROXY = os.getenv("TELEGRAM_PROXY")

# AWS S3 storage settings
AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
AWS_EXTERNAL_URL = os.getenv("AWS_EXTERNAL_URL").rstrip("/")

# VSEGPT API key
GPT_URL = os.getenv("GPT_URL")
GPT_API_TOKEN = os.getenv("GPT_API_TOKEN")
GPT_MODEL = os.getenv("GPT_MODEL")

# WEB parameters
HTTP_PORT = int(os.getenv("HTTP_PORT", "80"))
HTTPS_PORT = int(os.getenv("HTTPS_PORT", "443"))
SSL_CERT_PATH = os.getenv("SSL_CERT_PATH")
SSL_KEY_PATH = os.getenv("SSL_KEY_PATH")
URL_KEY = os.getenv("URL_KEY")
URL_BASE = os.getenv("URL_BASE")

# Miscellaneous constants
CountOfRecentBooks = 5
MaxBytesInCategoryName = 60 # 64 - len("cat")
MaxCharsInMessage = 4096
MaxButtonsInMessage = 60 # 80+ buttons got REPLY_MARKUP_TOO_LONG error from Telegram

# ========================================================
# Environment variables
# ========================================================

i18n = None  # Placeholder for i18n instance
FSMi18n = None  # Placeholder for FSMi18n instance

first_router = Router() # Router for global commands
base_router = Router() # Router for base commands
last_router = Router() # Router for trash messages

pool = None  # Placeholder for database connection pool

# ========================================================
# Start section
# ========================================================

# Logging configuration
logging.basicConfig(level=logging.INFO)

# ========================================================
# Routines defenitions
# ========================================================

# -------------------------------------------------------
# Remove inline keyboard from callback message or last stored in state
async def RemoveInlineKeyboards(callback: CallbackQuery, state: FSMContext, bot: Bot, event_chat: Chat) -> None:
    if callback:
        await callback.answer()
        await callback.message.edit_reply_markup(reply_markup=None)
    else:
        data = await state.get_data()
        inline = data.get("inline")
        if inline:
            inline_list = inline if isinstance(inline, list) else [inline]
            for message_id in inline_list:
                try:
                    await bot.edit_message_reply_markup(chat_id=event_chat.id, message_id=message_id, reply_markup=None)
                except Exception as e:
                    logging.error(f"Error deleting inline keyboard: {e}")
    await state.update_data(inline=None)

# -------------------------------------------------------
# Remove previous bot message in the chat
async def RemovePreviousBotMessage(state: FSMContext, bot: Bot, event_chat: Chat) -> None:
    data = await state.get_data()
    inline = data.get("inline")
    if inline:
        inline_list = inline if isinstance(inline, list) else [inline]
        for message_id in inline_list:
            try:
                await bot.delete_message(chat_id=event_chat.id, message_id=message_id)
            except Exception as e:
                logging.error(f"Error deleting previous bot message: {e}")
        await state.update_data(inline=None)

# -------------------------------------------------------
# Handler for trash messages
@last_router.message()
async def trash_entered(message: Message) -> None:
    await message.delete()

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