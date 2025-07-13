# ========================================================
# Module for handling bot messages related to manipulate cathegories
# ========================================================
import asyncpg # For asynchronous PostgreSQL connection
from aiogram import Bot, F # For Telegram bot framework
from aiogram import Router # For creating a router for handling messages
from aiogram.types import Message # For Telegram message handling
from aiogram.fsm.context import FSMContext # For finite state machine context
from aiogram.utils.i18n import gettext as _ # For internationalization and localization
from aiogram.types.callback_query import CallbackQuery # For handling callback queries
from aiogram.utils.keyboard import InlineKeyboardBuilder # For creating inline keyboards
from aiogram.filters.command import Command # For command handling

import modules.environment as env # For environment variables and configurations
import modules.h_start as h_start # For handling start command
import modules.h_cover as h_cover # For do book cover photos

# Router for handling messages related to manipulate cathegories
cat_router = Router()

# This function prepares and sends the inline keyboard for selecting a cathegory.
# It also sets the state for the bot to wait for the user's selection.
# The function takes the following additional parameters:
# - can_add: A boolean indicating if the user can add a new cathegory
# - action: The action, executed this routine (e.g., "add_book")
async def SelectCathegory(message: Message, userid: int, state: FSMContext, pool: asyncpg.Pool, bot: Bot, action: str) -> None:
    builder = InlineKeyboardBuilder()
    # Store can_add and action parameters in user data
    await state.update_data(action=action)
    if action == "add_book":
        await state.update_data(can_add=True)
    else:
        await state.update_data(can_add=False)
    await state.update_data(cathegory=None)
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
        """, userid)
        # If there are cathegories, create buttons for each one and ask user
        if result:
            if action == "add_book":
                text = _("select_or_enter_cathegory_add_book")
            elif action == "select_cat":
                text = _("select_cathegory_to_view_books")
            await env.RemoveOldInlineKeyboards(state, message.chat.id, bot)
            for row in result:
                builder.button(text=f"{row[0]}  ({row[1]})", callback_data=env.Cathegory(name=row[0]) )
            builder.adjust(1)
            sent_message = await message.answer(text, reply_markup=builder.as_markup())
            await state.update_data(inline=sent_message.message_id)
        else:
            # If there are no cathegories, check if the user can add a new one
            if action == "add_book":
                await message.answer(_("enter_cathegory_add_book"))
            else:
                await message.answer(_("no_books"))
                await h_start.MainMenu(message, state, pool, bot)
                await state.set_state(env.State.wait_for_command)
                return
        await state.set_state(env.State.select_cathegory)

# Handler for inline button selection of a cathegory
@cat_router.callback_query(env.Cathegory.filter())
async def cathegory_selected(callback: CallbackQuery, callback_data: env.Cathegory, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    await env.RemoveMyInlineKeyboards(callback, state)
    await DoCathegory(callback_data.name, callback.message, state, pool, bot)

# Handler for entered text when the user can add a new cathegory
@cat_router.message(env.State.select_cathegory, F.text)
async def cathegory_entered(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    data = await state.get_data()
    can_add = data.get("can_add")
    if can_add:
        await DoCathegory(message.text, message, state, pool, bot)
    else:
        await message.delete()
        await message.answer(_("can_not_add_cathegory"))

# Process the selected cathegory
async def DoCathegory(cathegory: str, message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    # Save selected cathegory
    await state.update_data(cathegory=cathegory)
    # Notify the user about the selected cathegory
    await message.answer(_("{cathegory}_selected").format(cathegory=cathegory))
    # Retrieve the action from the state
    data = await state.get_data()
    action = data.get("action")
    # Perform the action based on the selected cathegory
    if action == "add_book":
        await h_cover.AskForCover(message, state, pool, bot)
    elif action == "select_cat":
        await h_start.MainMenu(message, state, pool, bot)
    
# Handler for the /cat command
@env.first_router.message(Command("cat"))
async def add_command(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    await env.RemoveOldInlineKeyboards(state, message.chat.id, bot)
    await SelectCathegory(message, message.from_user.id, state, pool, bot, "select_cat")

# Handler for the callback query when the user selects "cat" from the main menu
@env.first_router.callback_query(env.MainMenu.filter(F.action=="cat"))
async def add_callback(callback: CallbackQuery, callback_data: env.MainMenu, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    await env.RemoveMyInlineKeyboards(callback, state)
    await SelectCathegory(callback.message, callback.from_user.id, state, pool, bot, "select_cat")