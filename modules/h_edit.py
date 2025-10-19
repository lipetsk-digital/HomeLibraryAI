# Module for edit values of book fields

from modules.imports import asyncpg, _, as_key_value, env, eng
from modules.imports import Bot, F, Chat, User, Message, ReactionTypeEmoji, InlineKeyboardBuilder, CallbackQuery, FSMContext
import modules.book as book # For save book to database

# -------------------------------------------------------
# Send message with inline-buttons of the book fields selection
async def SelectField(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
    await eng.RemoveInlineKeyboards(None, state, bot, event_chat)
    # Create new inline keyboard
    builder = InlineKeyboardBuilder()
    for field in env.BOOK_FIELDS:
        builder.button(text=_(field), callback_data=env.BookFields(field=field) )
    builder.adjust(1)
    # Add to the message with book information the keyboard
    sent_message = await message.answer(_("select_field"), reply_markup=builder.as_markup())
    await state.update_data(inline=sent_message.message_id)
    await state.set_state(env.State.select_field)

# -------------------------------------------------------
# Handle button of field selection
@eng.base_router.callback_query(env.BookFields.filter())
async def field_selected(callback: CallbackQuery, callback_data: env.BookFields, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
    await eng.RemoveInlineKeyboards(callback, state, bot, event_chat)
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

# -------------------------------------------------------
# Handler for entered text when the user edits field value
@eng.base_router.message(env.State.wait_for_field_value, F.text)
async def value_entered(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
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
    await eng.RemoveInlineKeyboards(None, state, bot, event_chat)
    builder = InlineKeyboardBuilder()
    for action in env.BRIEF_ACTIONS:
        builder.button(text=_(action), callback_data=env.BriefActions(action=action) )
    builder.adjust(2,1)
    # Add to the message with book information the keyboard
    await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=sent_message.message_id, reply_markup=builder.as_markup())
    await state.update_data(inline=sent_message.message_id)
    await state.set_state(env.State.wait_reaction_on_brief)

# -------------------------------------------------------
# Handler for edit buttons of books
@eng.base_router.callback_query(env.EditBook.filter())
async def edit_book_callback(callback: CallbackQuery, callback_data: env.EditBook, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
    book_id = callback_data.book_id
    user_id = callback.from_user.id
    # Fetch book information from the database
    async with pool.acquire() as connection:
        row = await connection.fetchrow("""
            SELECT *
            FROM books
            WHERE user_id = $1 AND book_id = $2
        """, user_id, book_id)
    if row:
        # Store book information in the state
        book_dict = {}
        for field in env.BOOK_FIELDS + env.ADVANCED_BOOK_FIELDS:
            book_dict[field] = row.get(field)
        await state.update_data(**book_dict)
        await state.update_data(book_id=book_id)
        sent_message = await book.PrintBook(callback.message, state, pool, bot)
        await SelectField(callback.message, state, pool, bot, event_chat)
    else:
        await callback.message.answer(_("book_not_found"))