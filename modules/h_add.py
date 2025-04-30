# ========================================================
# Module for handling bot messages related to adding a new book
# ========================================================
import asyncpg # For asynchronous PostgreSQL connection
from aiogram import Bot, F # For Telegram bot framework
from aiogram import Router # For creating a router for handling messages
from aiogram.types import Message # For Telegram message handling
from aiogram.fsm.context import FSMContext # For finite state machine context
from aiogram.filters.command import Command # For command handling
from aiogram.types.callback_query import CallbackQuery # For handling callback queries

import modules.environment as env # For environment variables and configurations

# Router for handling messages related to adding a new book
add_router = Router()

@add_router.message(Command("add"))
async def add_command(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    await message.answer("Please send me photo of the book cover for adding a new book...")

@add_router.callback_query(env.MainMenu.filter(F.action=="add"))
async def add_callback(event: CallbackQuery, callback_data: env.MainMenu, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    await event.message.edit_reply_markup(reply_markup=None)
    await event.message.answer("Please send me photo of the book cover for adding a new book...")
    await event.answer()