# ========================================================
# Module for handling bot messages related to changing the language
# ========================================================
import asyncpg # For asynchronous PostgreSQL connection
from aiogram import Bot, F # For Telegram bot framework
from aiogram import Router # For creating a router for handling messages
from aiogram.types import Message # For Telegram message handling
from aiogram.fsm.context import FSMContext # For finite state machine context
from aiogram.utils.i18n import gettext as _ # For internationalization and localization
from aiogram.filters.command import Command # For command handling
from aiogram.types.callback_query import CallbackQuery # For handling callback queries
from aiogram.utils.keyboard import InlineKeyboardBuilder # For creating inline keyboards
from babel import Locale

import modules.environment as env # For environment variables and configurations
import modules.h_start as h_start # For handling start command

# Router for handling messages related to changing the language
lang_router = Router()

# Handler for the /add command
@env.first_router.message(Command("settings"))
async def add_command(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    builder = InlineKeyboardBuilder()
    await env.RemoveOldInlineKeyboards(state, message.chat.id, bot)
    available_languages = sorted(env.i18n.available_locales)
    for lang in available_languages:
        locale = Locale.parse(lang)
        english_name = locale.english_name.split(" (")[0]  # Get the English name without the region
        native_name = locale.get_language_name(locale=lang)
        builder.button(text=english_name+' / '+native_name, callback_data=env.Language(lang=lang) )
    builder.adjust(1)
    sent_message = await message.answer(_("select_lang"), reply_markup=builder.as_markup())
    await state.update_data(inline=sent_message.message_id)
    await state.set_state(env.State.select_lang)

# Handler for the callback query when the user selects "add" from the main menu
@lang_router.callback_query(env.Language.filter())
async def lang_callback(callback: CallbackQuery, callback_data: env.Language, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    # Finish inline buttons
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await state.update_data(inline=None)
    # Change locale
    await env.FSMi18n.set_locale(state, callback_data.lang)
    # Get native name of selected language
    locale = Locale.parse(callback_data.lang)
    native_name = locale.get_language_name(locale=callback_data.lang)
    await callback.message.answer(_("{language}_selected").format(language=native_name))
    # Send the main menu again
    await h_start.MainMenu(callback.message, state, pool, bot)
