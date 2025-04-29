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
from aiogram.types import Message # For Telegram message handling
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

# Class for finite state machine
class Form(StatesGroup):
    wait_for_command = State()

# Main menu actions
MAIN_MENU_ACTIONS = {
    "add": "➕ Add book",
    "find": "🔍 Search",
    "edit": "✏️ Edit book",
    "cat": "⚙️ Cathegories",
    "export": "📨 Export"
}

# Callback factory for main menu
class MainMenu(CallbackData, prefix="main"):
    action: str