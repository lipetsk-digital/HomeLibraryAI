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
import modules.environment as env # For environment variables and configurations

addbook_router = Router()


@addbook_router.message(env.Form.wait_for_command)
async def doitall(message: Message, state: FSMContext, pool: asyncpg.Pool) -> None:
    await message.answer("State = wait_for_command! 😉")
    await state.set_state(env.Form.position)
    await state.update_data(full_name=message.from_user.full_name)
    data = await state.get_data()
    await message.answer("Full name = "+data.get('full_name'))


@addbook_router.message()
async def doitall(message: Message, state: FSMContext, pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO logs (userid, nickname, username) VALUES ($1, $2, $3)",
            message.from_user.id, message.from_user.username, message.from_user.full_name
        )
    await state.set_state(env.Form.wait_for_command)
    await state.update_data(first_name=message.from_user.first_name)
    await message.answer("State = position! 😉")

