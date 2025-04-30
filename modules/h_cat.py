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
# The function takes the following additional parameters:
# - can_add: A boolean indicating if the user can add a new cathegory
# - action: The action, executed this routine (e.g., "add_book")
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
                builder.button(text=f"{row[1]}  ({row[2]})", callback_data=env.Cathegory(name=row[1]) )
            builder.adjust(1)
            await message.answer(text, reply_markup=builder.as_markup())
        else:
            # If there are no cathegories, check if the user can add a new one
            if can_add:
                await message.answer("You have no cathegories in your library. Enter new cathegory name:", reply_markup=None)
            else:
                await message.answer("You have no cathegories in your library", reply_markup=None)
                await h_start.MainMenu(message, state, pool, bot)
                await state.set_state(env.State.wait_for_command)
                return
        await state.set_state(env.State.wait_select_cathegory)

# Handler for inline button selection of a cathegory
@cat_router.callback_query(env.Cathegory)
async def cathegory_selected(callback: CallbackQuery, callback_data: env.Cathegory, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await DoCathegory(callback_data.name, callback.message, state, pool, bot)

# Handler for entered text when the user can add a new cathegory
@cat_router.message(env.State.wait_select_cathegory, F.text)
async def cathegory_entered(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    data = await state.get_data()
    can_add = data.get("can_add")
    if can_add:
        await DoCathegory(message.text, message, state, pool, bot)
    else:
        await message.delete()
        await message.answer("You cannot add a new cathegory at this moment. Please select an existing one")

# Handler for non-text messages when the bot is in the wait_select_cathegory state
@cat_router.message(env.State.wait_select_cathegory)
async def trash_entered(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    await message.delete()
    await message.answer("Please send a valid cathegory name")

# Process the selected cathegory
async def DoCathegory(cathegory: str, message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    # Save selected cathegory
    await state.update_data(cathegory=cathegory)
    # Notify the user about the selected cathegory
    await message.answer(f"You selected the cathegory: {cathegory}")
    # Retrieve the action from the state
    data = await state.get_data()
    action = data.get("action")
    # Perform the action based on the selected cathegory
    if action == "add_book":
        await message.answer("Please enter the book details to add to this cathegory.")
        await state.set_state(env.State.wait_for_cover_photo)
