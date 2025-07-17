from aiogram.types import FSInputFile

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
from aiogram.utils.formatting import Text, as_list, as_key_value # For formatting messages
from aiogram.types import BufferedInputFile
import random

import modules.environment as env # For environment variables and configurations
import modules.h_start as h_start # For main menu

# Send to user current book information from user's data and return Message object
async def PrintBook(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> Message:
    # Get the book data from the state
    data = await state.get_data() # Get stored user's data
    items = []
    # Loop through the book fields and add them to the items list
    for field in env.BOOK_FIELDS:
        if field in data:
            value = data[field]
            items.append(as_key_value(_(field), value))
    content = as_list(*items)
    # Send the message with the book information and the keyboard
    sent_message = await message.answer(**content.as_kwargs())
    return sent_message

# Save book to database
async def SaveBookToDatabase(callback: CallbackQuery, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    user_id = callback.from_user.id # Get the user ID from the callback
    # Get stored user's data
    data = await state.get_data()
    # Select max book_id of current user from the database
    async with pool.acquire() as connection:
        result = await connection.fetchval("SELECT COALESCE(MAX(book_id),0) FROM books WHERE user_id = $1", user_id)
        book_id = result + 1 # Increment the max book_id by 1
    # Build book dictionary
    fields = env.BOOK_FIELDS + env.ADVANCED_BOOK_FIELDS
    for field in fields:
        if field not in data:
            data[field] = None
    # Add manual fields
    data["user_id"] = user_id # Add user ID to the book data            
    data["book_id"] = book_id # Add book ID to the book data
    await state.update_data(book_id=book_id) # Save book ID in the state
    # Insert the book data into the database
    async with pool.acquire() as connection:
        await connection.execute(
            f"INSERT INTO books ({', '.join(fields)}) VALUES ({', '.join(['$' + str(i + 1) for i in range(len(fields))])})",
            *[data[field] for field in fields]
        )

# Loop through books dataset and send to user the books list
async def PrintBooksList(rows: list, message: Message, bot: Bot) -> None:
    # For short list of the books:
    if len(rows) == 0:
        await message.answer(_("no_books_found"))
    elif len(rows) < 10:
        await message.answer(_("{books}_found","{books}_founds",len(rows)).format(books=len(rows)))
        # Send one message for each book with title, authors, year and cover photo
        for row in rows:
            book_id = row.get("book_id")
            title = row.get("title")
            authors = row.get("authors")
            year = row.get("year")
            photo = row.get("cover_filename")  # Adjust field name as needed
            if photo:
                photo_url = env.AWS_EXTERNAL_URL + "/" + photo
                await message.answer_photo(photo=photo_url, caption=f"{book_id}. {title} - {authors}, {year}")
            else:
                await message.answer(title)
    else:
        # Send one message for all books with HTML formatting
        message_text = _("{books}_found","{books}_founds",len(rows)).format(books=len(rows))+"\n"
        for row in rows:
            book_id = row.get("book_id")
            title = row.get("title")
            authors = row.get("authors")
            year = row.get("year")
            emoji = random.choice(["📕", "📘", "📗", "📙"])
            message_text += f"{emoji} {book_id}. <b>{title}</b> - {authors}, {year}\n"
        await message.answer(message_text, parse_mode="HTML")
