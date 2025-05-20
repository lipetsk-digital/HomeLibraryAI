# ========================================================
# Module for edit a book information
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

# Prepare and send the inline-buttons of the book fields for the user
async def SelectField(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    await env.RemoveOldInlineKeyboards(state, message.chat.id, bot)
    # Create new inline keyboard
    builder = InlineKeyboardBuilder()
    for action in env.BOOK_FIELDS:
        builder.button(text=_(action), callback_data=env.BriefActions(action=action) )
    builder.adjust(1)
    # Add to the message with book information the keyboard
    sent_message = await message.answer(_("select_field"), reply_markup=builder.as_markup())
    await state.update_data(inline=sent_message.message_id)
    await state.set_state(env.State.select_field)
