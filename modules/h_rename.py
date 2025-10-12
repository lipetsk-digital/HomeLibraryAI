# ========================================================
# Module for handling bot messages related to renaming a cathegory
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

# Router for handling messages related to renaming a cathegory
rename_router = Router()

# Handler for the /rename command
@env.first_router.message(Command("rename"))
async def rename_command(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    await env.RemoveOldInlineKeyboards(state, message.chat.id, bot)
    await h_cat.SelectCathegory(message, message.from_user.id, state, pool, bot, "rename_cathegory")

