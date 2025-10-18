# ========================================================
# Module for handling bot messages related to recently added books
# ========================================================
import asyncpg # For asynchronous PostgreSQL connection
from aiogram import Bot, F # For Telegram bot framework
from aiogram import Router # For creating a router for handling messages
from aiogram.types import Message # For Telegram message handling
from aiogram.fsm.context import FSMContext # For finite state machine context
from aiogram.utils.i18n import gettext as _ # For internationalization and localization
from aiogram.filters.command import Command # For command handling
from aiogram.types.callback_query import CallbackQuery # For handling callback queries
from babel import Locale # For handling locale and language names

import modules.environment as env # For environment variables and configurations
import modules.h_start as h_start # For main menu
import modules.book as book # For generating list of the books

# Router for handling messages related to recently added books
#history_router = Router()

# Handler for the /history command
@env.first_router.message(Command("history"))
async def add_command(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    await env.RemoveOldInlineKeyboards(state, message.chat.id, bot)
    await recent_books(message, state, pool, bot, message.from_user.id)
 
# Handler for the callback query when the user selects "history" from the main menu
@env.first_router.callback_query(env.MainMenu.filter(F.action=="history"))
async def add_callback(callback: CallbackQuery, callback_data: env.MainMenu, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    await env.RemoveMyInlineKeyboards(callback, state)
    await recent_books(callback.message, state, pool, bot, callback.from_user.id)
 
# Handler for entered text when the user enters a search query
async def recent_books(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot, user_id: int) -> None:

    # Prepare the query to search for books by title using full-text search
    query = """
    SELECT book_id, title, authors, year, cover_filename
    FROM books
    WHERE user_id = $1
    ORDER BY book_id DESC
    LIMIT 5;
    """
    # Run the query to search for books in the database
    rows = await pool.fetch(query, user_id)
    await book.PrintBooksList(rows, message, bot)

    # Send main menu to the user
    await h_start.MainMenu(message, state, pool, bot)