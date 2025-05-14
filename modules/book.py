# ========================================================
# Module for save a book to database
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
import modules.h_start as h_start # For main menu

# Prepare and send the main menu inline-buttons for the user
async def SaveBookToDatabase(callback: CallbackQuery, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    user_id = callback.from_user.id # Get the user ID from the callback
    # Get stored user's data
    data = await state.get_data()
    # Select max book_id of current user from the database
    async with pool.acquire() as connection:
        result = await connection.fetchrow("SELECT MAX(book_id) FROM books WHERE user_id = $1", user_id)
        if result is None:
            book_id = 1 # If no book exists, set book_id to 1
        else:
            book_id = result[0] + 1 # Otherwise, increment the max book_id by 1
    # Build book dictionary
    fields = env.BOOK_FIELDS + env.ADVANCED_BOOK_FIELDS
    for field in fields:
        if field not in data:
            data[field] = None
    # Add manual fields
        data["user_id"] = user_id # Add user ID to the book data            
        data["book_id"] = book_id # Add book ID to the book data
    # Insert the book data into the database
    async with pool.acquire() as connection:
        await connection.execute(
            f"INSERT INTO books ({', '.join(fields)}) VALUES ({', '.join(['$' + str(i + 1) for i in range(len(fields))])})",
            *[data[field] for field in fields]
        )



