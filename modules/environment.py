# ========================================================
# Module for environment variables and configurations
# ========================================================
# This module is responsible for loading environment variables and configurations for the bot.
# It includes:
# - PostgreSQL connection settings
# - Logging configuration
# - Telegram bot token
# - Class for finite state machine (FSM) of the bot
# ========================================================

import os # For environment variables
import logging # For logging
from aiogram import Bot # For Telegram bot framework
from aiogram import Router # For creating a router for handling messages
from aiogram.fsm.context import FSMContext # For finite state machine context
from aiogram.fsm.state import State, StatesGroup # For finite state machine of Telegram-bot
from aiogram.filters.callback_data import CallbackData # For callback data handling


# PostgreSQL connection settings
POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "database": os.getenv("POSTGRES_DATABASE"),
    "user": os.getenv("POSTGRES_USERNAME"),
    "password": os.getenv("POSTGRES_PASSWORD")
}

# Logging configuration
logging.basicConfig(level=logging.INFO)

# Telegram bot token
TOKEN = os.getenv("TELEGRAM_TOKEN")

# AWS S3 storage settings
AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

# Class for finite state machine
class State(StatesGroup):
    wait_for_command = State()
    select_lang = State()
    select_cathegory = State()
    wait_for_cover_photo = State()

# Dummy function for pybabel to detect translatable strings
def _translate_(text: str) -> str:
    return text

i18n = None  # Placeholder for i18n instance
FSMi18n = None  # Placeholder for FSMi18n instance

first_router = Router() # Router for global commands
last_router = Router() # Router for trash messages

# Main menu actions
MAIN_MENU_ACTIONS = {
    "add": _translate_("add"),
    "find": _translate_("find"),
    "edit": _translate_("edit"),
    "cat": _translate_("cat"),
    "export": _translate_("export")
}
ADVANCED_ACTIONS = {
    "settings": _translate_("settings")
}

# Callback factory for main menu
class MainMenu(CallbackData, prefix="main"):
    action: str

# Callback factory for cathegory selection
class Cathegory(CallbackData, prefix="cat"):
    name: str

# Callback factory for language selection
class Language(CallbackData, prefix="lang"):
    lang: str

# Remove old inline keyboards from messages in the chat
async def RemoveOldInlineKeyboards(state: FSMContext, chat_id: int, bot: Bot) -> None:
    data = await state.get_data()
    inline = data.get("inline")
    if inline:
        try:
            await bot.edit_message_reply_markup(chat_id=chat_id, message_id=inline, reply_markup=None)
        except Exception as e:
            logging.error(f"Error deleting inline keyboard: {e}")
