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
from aiogram.types.callback_query import CallbackQuery # For handling callback queries
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
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# AWS S3 storage settings
AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

# VSEGPT API key
GPT_URL = os.getenv("GPT_URL")
GPT_API_TOKEN = os.getenv("GPT_API_TOKEN")
GPT_MODEL = os.getenv("GPT_MODEL")

# Class for finite state machine
class State(StatesGroup):
    wait_for_command = State()
    select_lang = State()
    select_cathegory = State()
    wait_for_cover_photo = State()
    wait_reaction_on_cover = State()
    wait_for_brief_photo = State()
    wait_reaction_on_brief = State()
    wait_next_book = State()

i18n = None  # Placeholder for i18n instance
FSMi18n = None  # Placeholder for FSMi18n instance

first_router = Router() # Router for global commands
last_router = Router() # Router for trash messages

# Dummy function for pybabel to detect translatable strings
def _translate_(text: str) -> str:
    return text

# Main menu actions
MAIN_MENU_ACTIONS = [
    _translate_("add"),
    _translate_("find"),
    _translate_("edit"),
    _translate_("cat"),
    _translate_("export")
]
ADVANCED_ACTIONS = [
    _translate_("settings")
]
COVER_ACTIONS = [
    _translate_("use_cover"),
    _translate_("use_original_photo"),
    _translate_("take_new_photo")
]
BOOK_FIELDS = [
    _translate_("title"),
    _translate_("authors"),
    _translate_("authors_full_names"),
    _translate_("pages"),
    _translate_("publisher"),
    _translate_("year"),
    _translate_("isbn"),
    _translate_("brief"),
    _translate_("annotation")
]
ADVANCED_BOOK_FIELDS = [
    "user_id",
    "book_id",
    "cathegory",
    "photo_filename",
    "cover_filename",
    "brief_filename"
]
BOOK_PROMPT = [
    _translate_("prompt_photo"),
    _translate_("prompt_result"),
    _translate_("prompt_count"),
    _translate_("prompt_lang"),
    _translate_("prompt_characters"),
    _translate_("prompt_plaintext"),
    _translate_("prompt_fields"),
    _translate_("prompt_title"),
    _translate_("prompt_authors"),
    _translate_("prompt_pages"),
    _translate_("prompt_publisher"),
    _translate_("prompt_year"),
    _translate_("prompt_isbn"),
    _translate_("prompt_annotation"),
    _translate_("prompt_brief"),
    _translate_("prompt_authors_full_names")
]
BRIEF_ACTIONS = [
    _translate_("use_brief"),
    _translate_("edit_brief"),
    _translate_("take_new_photo")
]
NEXT_ACTIONS = [
    _translate_("add_another_book"),
    _translate_("no_another_book")
]

# Callback factory for main menu
class MainMenu(CallbackData, prefix="main"):
    action: str

# Callback factory for cathegory selection
class Cathegory(CallbackData, prefix="cat"):
    name: str

# Callback factory for language selection
class Language(CallbackData, prefix="lang"):
    lang: str

# Callback factory for cover actions
class CoverActions(CallbackData, prefix="cover"):
    action: str

# Callback factory for the annotation page actions
class BriefActions(CallbackData, prefix="brief"):
    action: str

# Callback factory for the next actions
class NextActions(CallbackData, prefix="next"):
    action: str

# Finish handlers and remove current inline keyboard from its message
async def RemoveMyInlineKeyboards(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await state.update_data(inline=None)
                                   
# Remove old inline keyboards from messages in the chat
async def RemoveOldInlineKeyboards(state: FSMContext, chat_id: int, bot: Bot) -> None:
    data = await state.get_data()
    inline = data.get("inline")
    if inline:
        try:
            await state.update_data(inline=None)
            await bot.edit_message_reply_markup(chat_id=chat_id, message_id=inline, reply_markup=None)
        except Exception as e:
            logging.error(f"Error deleting inline keyboard: {e}")
