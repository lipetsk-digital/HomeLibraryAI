# ========================================================
# Module for handling bot messages related to start bot
# ========================================================
# This module is responsible for handling the /start command and sending the main menu to the user.
# It includes:
# - Handler for the /start command
# - Function to prepare and send the main menu inline-buttons
# - Function to prepare the bot's bottom left main menu commands
# - Function to send a brief statistic about the user's library
# ========================================================
import asyncpg # For asynchronous PostgreSQL connection
from aiogram import Bot # For Telegram bot framework
from aiogram.types import Message # For Telegram message handling
from aiogram.fsm.context import FSMContext # For finite state machine context
from aiogram.utils.i18n import gettext as _ # For internationalization and localization
from aiogram.filters.command import Command # For command handling
from aiogram.utils.keyboard import InlineKeyboardBuilder # For creating inline keyboards
from aiogram.types import BotCommand, BotCommandScopeDefault # For setting bot commands

import modules.environment as env # For environment variables and configurations

# Handler for the /start command
# This handler is triggered when the user sends the /start command.
# It logs the user information into the database and sends a brief statistic about the user's library.
# It also send the main menu for the user.
@env.first_router.message(Command("start"))
async def start_command(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO logs (user_id, nickname, username) VALUES ($1, $2, $3)",
            message.from_user.id, message.from_user.username, message.from_user.full_name
        )
    await BriefStatistic(message, message.from_user.id, state, pool, bot)
    await MainMenu(message, state, pool, bot)

# Prepare and send the main menu inline-buttons for the user
async def MainMenu(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    builder = InlineKeyboardBuilder()
    await env.RemoveOldInlineKeyboards(state, message.chat.id, bot)
    for action in env.MAIN_MENU_ACTIONS:
        builder.button(text=_(action), callback_data=env.MainMenu(action=action) )
    builder.adjust(2, 3)
    sent_message = await message.answer(_("main_menu"), reply_markup=builder.as_markup())
    await state.update_data(inline=sent_message.message_id)
    await state.set_state(env.State.wait_for_command)

# Prepare the bot's bottom left main menu commands
async def PrepareMenu(bot: Bot):
    # Loop through all available languages and set the bot commands for each one    
    available_languages = env.i18n.available_locales
    env.logging.debug(f"Available languages: {available_languages}")
    for lang in available_languages:
        commands = []
        actions = env.MAIN_MENU_ACTIONS + env.ADVANCED_ACTIONS
        for action in actions:
            commands.append(BotCommand(command=action, description=env.i18n.gettext(action, locale=lang)))
        await bot.set_my_commands(commands, BotCommandScopeDefault(), lang)

# Send a brief statistic about the user's library
async def BriefStatistic(message: Message, userid: int, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    async with pool.acquire() as conn:
        result = await conn.fetchval("""SELECT count(*) FROM books WHERE "user_id"=$1""", userid)
    if (result is None) or (result == 0):
        await message.answer(_("no_books"))
    else:
        await message.answer(_("{result}_book","{result}_books",result).format(result=result))

# Handler for trash messages
@env.last_router.message()
async def trash_entered(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    await message.delete()