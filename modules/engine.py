# Module for configuraion data, environment variables, and basic routines

from modules.imports import Bot, env, Router, CallbackQuery, FSMContext, Chat, Message

import os # For environment variables
import logging # For logging

from aiogram.types import BotCommand, BotCommandScopeDefault # For setting bot commands

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

# AWS S3 storage settings
AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
AWS_EXTERNAL_URL = os.getenv("AWS_EXTERNAL_URL").rstrip("/")

# VSEGPT API key
GPT_URL = os.getenv("GPT_URL")
GPT_API_TOKEN = os.getenv("GPT_API_TOKEN")
GPT_MODEL = os.getenv("GPT_MODEL")

# ========================================================
# Environment variables
# ========================================================

i18n = None  # Placeholder for i18n instance
FSMi18n = None  # Placeholder for FSMi18n instance

first_router = Router() # Router for global commands
last_router = Router() # Router for trash messages

# ========================================================
# Start section
# ========================================================

# Logging configuration
logging.basicConfig(level=logging.INFO)

# ========================================================
# Routines defenitions
# ========================================================

# -------------------------------------------------------
# Prepare the bot's bottom left main menu commands
async def PrepareGlobalMenu(bot: Bot):
    # Loop through all available languages and set the bot commands for each one    
    available_languages = i18n.available_locales
    logging.debug(f"Available languages: {available_languages}")
    for lang in available_languages:
        commands = []
        actions = env.MAIN_MENU_ACTIONS + env.ADVANCED_ACTIONS
        for action in actions:
            commands.append(BotCommand(command=action, description=i18n.gettext(action, locale=lang)))
        await bot.set_my_commands(commands, BotCommandScopeDefault(), lang)


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
            try:
                await bot.edit_message_reply_markup(chat_id=event_chat.id, message_id=inline, reply_markup=None)
            except Exception as e:
                logging.error(f"Error deleting inline keyboard: {e}")
    await state.update_data(inline=None)

# -------------------------------------------------------
# Handler for trash messages
@last_router.message()
async def trash_entered(message: Message) -> None:
    await message.delete()
