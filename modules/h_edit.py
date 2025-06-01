# ========================================================
# Module for edit value of book field
# ========================================================
import asyncpg # For asynchronous PostgreSQL connection
from aiogram import Bot, F # For Telegram bot framework
from aiogram import Router # For creating a router for handling messages
from aiogram.types import Message, ReactionTypeEmoji # For Telegram message handling
from aiogram.fsm.context import FSMContext # For finite state machine context
from aiogram.utils.i18n import gettext as _ # For internationalization and localization
from aiogram.filters.command import Command # For command handling
from aiogram.types.callback_query import CallbackQuery # For handling callback queries
from aiogram.utils.keyboard import InlineKeyboardBuilder # For creating inline keyboards
from aiogram.utils.formatting import Text, as_list, as_key_value # For formatting messages

import modules.environment as env # For environment variables and configurations
import modules.book as book # For save book to database

# Router for handling messages related to selecting book fields
edit_router = Router()

# Handler for entered text when the user can add a new cathegory
@edit_router.message(env.State.wait_for_field_value, F.text)
async def value_entered(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    # Extract information about field editing
    data = await state.get_data()
    field = data.get("field")
    value = message.text
    book_dict = {}
    book_dict[field] = value
    # Moify the book information in the user's state
    await state.update_data(**book_dict)
    # Get like to user's input
    await bot.set_message_reaction(chat_id=message.chat.id,
                                    message_id=message.message_id,
                                    reaction=[ReactionTypeEmoji(emoji='👍')])
    # Print current book information
    sent_message = await book.PrintBook(message, state, pool, bot)
    # Generate keyboard with further actions
    builder = InlineKeyboardBuilder()
    await env.RemoveOldInlineKeyboards(state, message.chat.id, bot)
    for action in env.BRIEF_ACTIONS:
        builder.button(text=_(action), callback_data=env.BriefActions(action=action) )
    builder.adjust(2,1)
    # Add to the message with book information the keyboard
    await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=sent_message.message_id, reply_markup=builder.as_markup())
    await state.update_data(inline=sent_message.message_id)
    await state.set_state(env.State.wait_reaction_on_brief)