# ========================================================
# Module for handling bot messages related to asking for next book
# ========================================================
import asyncpg # For asynchronous PostgreSQL connection
from aiogram import Bot, F # For Telegram bot framework
from aiogram import Router # For creating a router for handling messages
from aiogram.types import Message # For Telegram message handling
from aiogram.fsm.context import FSMContext # For finite state machine context
from aiogram.utils.i18n import gettext as _ # For internationalization and localization
from aiogram.filters.command import Command # For command handling
from aiogram.types.callback_query import CallbackQuery # For handling callback queries
from aiogram.utils.keyboard import InlineKeyboardBuilder # For creating inline keyboards

import modules.environment as env # For environment variables and configurations
import modules.h_start as h_start # For handling start command
import modules.h_cover as h_cover # For do book cover photos

# Router for handling messages related to asking for the next book
next_router = Router()

# Handler for the callback query when the user selects "add another book"
@next_router.callback_query(env.NextActions.filter(F.action == "add_another_book"))
async def add_another_book(callback: CallbackQuery, callback_data: env.Language, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    # Finish inline buttons
    await env.RemoveMyInlineKeyboards(callback, state)
    # Go to adding another book
    await h_cover.AskForCover(callback.message, state, pool, bot)

# Handler for the callback query when the user selects "do not add another book"
@next_router.callback_query(env.NextActions.filter(F.action == "no_another_book"))
async def no_another_book(callback: CallbackQuery, callback_data: env.Language, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    # Finish inline buttons
    await env.RemoveMyInlineKeyboards(callback, state)
    # Send the main menu again
    await h_start.MainMenu(callback.message, state, pool, bot)
