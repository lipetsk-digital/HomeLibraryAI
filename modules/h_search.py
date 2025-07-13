# ========================================================
# Module for handling bot messages related to search a book
# ========================================================
import asyncpg # For asynchronous PostgreSQL connection
from aiogram import Bot, F # For Telegram bot framework
from aiogram import Router # For creating a router for handling messages
from aiogram.types import Message # For Telegram message handling
from aiogram.fsm.context import FSMContext # For finite state machine context
from aiogram.utils.i18n import gettext as _ # For internationalization and localization
from aiogram.filters.command import Command # For command handling
from aiogram.types.callback_query import CallbackQuery # For handling callback queries
from babel import Locale

import modules.environment as env # For environment variables and configurations
import modules.h_cat as h_cat # For manipulating cathegories
import modules.h_start as h_start # For main menu

# Router for handling messages related to search a book
search_router = Router()

# Handler for the /search command
@env.first_router.message(Command("search"))
async def add_command(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    await env.RemoveOldInlineKeyboards(state, message.chat.id, bot)
    await message.answer(_("enter_search_query"))
    await state.set_state(env.State.wait_for_search_query)

# Handler for the callback query when the user selects "add" from the main menu
@search_router.callback_query(env.MainMenu.filter(F.action=="search"))
async def add_callback(callback: CallbackQuery, callback_data: env.MainMenu, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    await env.RemoveMyInlineKeyboards(callback, state)
    await callback.message.answer(_("enter_search_query"))
    await state.set_state(env.State.wait_for_search_query)

# Handler for entered text when the user enters a search query
@search_router.message(env.State.wait_for_search_query, F.text)
async def search_query_entered(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:

    # Prepare the query to search for books by title using full-text search
    query = """
    SELECT book_id, title, authors, year
    FROM books
    WHERE user_id=$1 AND
    (
      to_tsvector($2, title) @@ plainto_tsquery($2, $3) OR
      to_tsvector($2, authors_full_names) @@ plainto_tsquery($2, $3)
    );
    """
    user_id = message.from_user.id # Get the user ID from the message
    lang = (await state.get_data()).get("locale", "en") # Get the user's locale from the state, default to "en"
    locale = Locale.parse(lang) # Convert two-letter locale code to full locale name for PostgreSQL full-text search
    language = locale.get_language_name('en').lower() # Convert to lowercase for consistency
    search_text = message.text.strip()

    # Run the query to search for books in the database
    rows = await pool.fetch(query, user_id, language, search_text)
    if rows:
        result = "\n".join([f"{row['book_id']}. {row['title']} - {row['authors']}, {row['year']}" for i, row in enumerate(rows)])
    else:
        result = _("no_books_found")

    # Send the result of the search to the user
    await message.answer(result)
    # Send main menu to the user
    await h_start.MainMenu(message, state, pool, bot)