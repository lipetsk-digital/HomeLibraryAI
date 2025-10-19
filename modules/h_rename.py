# ========================================================
# Module for handling bot messages related to renaming a category
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
import modules.h_cat as h_cat # For manipulating cathegories
import modules.h_start as h_start # For handling start command

# Router for handling messages related to renaming a category
rename_router = Router()

# Handler for the /rename command
@env.first_router.message(Command("rename"))
async def rename_command(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    await env.RemoveOldInlineKeyboards(state, message.chat.id, bot)
    await h_cat.SelectCategory(message, message.from_user.id, state, pool, bot, "rename_category")

# Handler for entered text when the user enters new category name
@rename_router.message(env.State.wait_for_new_category_name, F.text)
async def new_cat_name_entered(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    # Extract information about field editing
    data = await state.get_data()
    old_cat = data.get("category")
    new_cat = message.text
    # Rename category in the database
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE books
            SET category = $1
            WHERE user_id = $2 AND category = $3
        """, new_cat, message.from_user.id, old_cat)
    # Acknowledge the renaming
    await message.answer(_("category_renamed"))
    # Return to the main menu
    await h_start.MainMenu(message, state, pool, bot)