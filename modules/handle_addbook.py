# ========================================================
# Module for handling bot messages related to adding books
# ========================================================
# This module creates a router for handling messages related to adding books to the database
# It includes:
# ========================================================

from aiogram.types import Message # For Telegram message handling
from aiogram.fsm.context import FSMContext # For finite state machine context
from aiogram import Router # For creating a router for handling messages
import asyncpg # For asynchronous PostgreSQL connection

addbook_router = Router()

@addbook_router.message()
async def doitall(message: Message, state: FSMContext, pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO logs (userid, nickname, username) VALUES ($1, $2, $3)",
            message.from_user.id, message.from_user.username, message.from_user.full_name
        )
    await message.answer("I remember you! 😉")

