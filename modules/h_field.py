# ========================================================
# Module for select book fields
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
from aiogram.utils.formatting import Text, as_list, as_key_value # For formatting messages

import modules.environment as env # For environment variables and configurations

# Router for handling messages related to selecting book fields
field_router = Router()

# Send message with inline-buttons of the book fields selection
async def SelectField(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    await env.RemoveOldInlineKeyboards(state, message.chat.id, bot)
    # Create new inline keyboard
    builder = InlineKeyboardBuilder()
    for field in env.BOOK_FIELDS:
        builder.button(text=_(field), callback_data=env.BookFields(field=field) )
    builder.adjust(1)
    # Add to the message with book information the keyboard
    sent_message = await message.answer(_("select_field"), reply_markup=builder.as_markup())
    await state.update_data(inline=sent_message.message_id)
    await state.set_state(env.State.select_field)

# Handle button of field selection
@field_router.callback_query(env.BookFields.filter())
async def field_selected(callback: CallbackQuery, callback_data: env.Cathegory, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    await env.RemoveMyInlineKeyboards(callback, state)
    # Print current value of selected field
    field = callback_data.field
    await state.update_data(field=field)
    data = await state.get_data()
    if field in data:
        value = data[field]
        if value:
            content = as_key_value(_(field), _("edit_field_value"))
            await callback.message.answer(**content.as_kwargs())
            await callback.message.answer(value)
        else:
            content = as_key_value(_(field), _("edit_field_empty"))
            await callback.message.answer(**content.as_kwargs())
    else:
        content = as_key_value(_(field), _("edit_field_empty"))
        await callback.message.answer(**content.as_kwargs())
    # Wait for new value of selected field
    await state.set_state(env.State.wait_for_field_value)
