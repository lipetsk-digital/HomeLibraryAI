# ========================================================
# Module for handling bot messages related to manipulate cathegories
# ========================================================
import asyncpg # For asynchronous PostgreSQL connection
from aiogram import Bot, F # For Telegram bot framework
from aiogram import Router # For creating a router for handling messages
from aiogram.types import Message # For Telegram message handling
from aiogram.fsm.context import FSMContext # For finite state machine context
from aiogram.filters.command import Command # For command handling
from aiogram.types.callback_query import CallbackQuery # For handling callback queries
from aiogram.utils.keyboard import InlineKeyboardBuilder # For creating inline keyboards

import modules.environment as env # For environment variables and configurations
import modules.h_start as h_start # For handling start command

# Router for handling messages related to manipulate cathegories
cat_router = Router()

# This function prepares and sends the inline keyboard for selecting a cathegory.
# It also sets the state for the bot to wait for the user's selection.
async def SelectCathegory(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot, can_add: bool, action: str, text: str) -> None:
    builder = InlineKeyboardBuilder()
    # Store can_add and action parameters in user data
    await state.update_data(can_add=can_add, action=action)
    # Select cathegories from the database
    async with pool.acquire() as conn:
        # Fetching cathegories from the database
        # The query selects the cathegory and counts the number of books in each cathegory for the user.
        # It groups the results by cathegory and orders them by the count of books in descending order.
        result = await conn.fetch("""
            SELECT b.cathegory, COUNT(*) as book_count
            FROM books b
            WHERE b.user_id = $1
            GROUP BY b.cathegory
            ORDER BY book_count DESC
        """, message.from_user.id)
        # If there are cathegories, create buttons for each one and ask user
        if result:
            for row in result:
                builder.button(text=row[1]+' ('+row[2]+')', callback_data=env.Cathegory(name=row[1]) )
            builder.adjust(1)
            await message.answer(text, reply_markup=builder.as_markup())
        else:
            if can_add:
                await message.answer("You have no cathegories in your library. Enter new cathegory name:", reply_markup=None)
            else:
                await message.answer("You have no cathegories in your library", reply_markup=None)
                await h_start.MainMenu(message, state, pool, bot)
                await state.set_state(env.State.wait_for_command)
                return
        await state.set_state(env.State.wait_select_cathegory)