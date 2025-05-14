# ========================================================
# Module for handling bot messages related to adding a new book
# ========================================================
import asyncpg # For asynchronous PostgreSQL connection
from aiogram import Bot, F # For Telegram bot framework
from aiogram import Router # For creating a router for handling messages
from aiogram.types import Message # For Telegram message handling
from aiogram.fsm.context import FSMContext # For finite state machine context
from aiogram.utils.i18n import gettext as _ # For internationalization and localization
from aiogram.filters.command import Command # For command handling
from aiogram.types.callback_query import CallbackQuery # For handling callback queries

import modules.environment as env # For environment variables and configurations
import modules.h_cat as h_cat # For manipulating cathegories

# Router for handling messages related to adding a new book
add_router = Router()

# Handler for the /add command
@env.first_router.message(Command("add"))
async def add_command(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    await env.RemoveOldInlineKeyboards(state, message.chat.id, bot)
    await message.answer(_("start_add_book"))
    await h_cat.SelectCathegory(message, state, pool, bot, "add_book")

# Handler for the callback query when the user selects "add" from the main menu
@add_router.callback_query(env.MainMenu.filter(F.action=="add"))
async def add_callback(callback: CallbackQuery, callback_data: env.MainMenu, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    await env.RemoveMyInlineKeyboards(callback, state)
    await callback.message.answer(_("start_add_book"))
    await h_cat.SelectCathegory(callback.message, state, pool, bot, "add_book")