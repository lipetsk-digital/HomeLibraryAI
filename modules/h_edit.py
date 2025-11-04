# Module for edit values of book fields

from email.mime import message
from modules.imports import asyncpg, _, as_key_value, env, eng
from modules.imports import Bot, F, Chat, User, Message, ReactionTypeEmoji, InlineKeyboardBuilder, CallbackQuery, FSMContext
import modules.book as book # For save book to database
import modules.h_cat as h_cat # For category selection routines
import modules.h_start as h_start # For main menu routines
import modules.h_brief as h_brief # For brief routines

# -------------------------------------------------------
# Send message with inline-buttons of the book fields selection
async def SelectField(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
    await eng.RemoveInlineKeyboards(None, state, bot, event_chat)
    data = await state.get_data()
    action = data.get("action")
    # Create new inline keyboard
    builder = InlineKeyboardBuilder()
    if action == "edit_book":
        fields = env.PUBLIC_BOOK_FIELDS + env.BOOK_ACTIONS
    else:
        fields = env.PUBLIC_BOOK_FIELDS + ["cancel"]
    for field in fields:
        builder.button(text=_(field), callback_data=env.BookFields(field=field))
    builder.adjust(2)
    # Add to the message with book information the keyboard
    sent_message = await message.answer(_("select_field"), reply_markup=builder.as_markup())
    await state.update_data(inline=sent_message.message_id)
    await state.set_state(env.State.select_field)

# -------------------------------------------------------
# Handle button of field selection
@eng.base_router.callback_query(env.BookFields.filter())
async def field_selected(callback: CallbackQuery, callback_data: env.BookFields, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    await eng.RemoveInlineKeyboards(callback, state, bot, event_chat)
    field = callback_data.field
    data = await state.get_data()
    action = data.get("action")
    # Handle special books actions
    if field == "move_book":
        await h_cat.SelectCategory(state, pool, bot, event_chat, event_from_user)
    elif field == "delete_book":
        builder = InlineKeyboardBuilder()
        for action in env.CONFIRM_DELETE:
            builder.button(text=_(action), callback_data=env.ConfirmDelete(action=action))
        builder.adjust(2)
        sent_message = await callback.message.answer(_("confirm_delete_book"), reply_markup=builder.as_markup())
        await state.update_data(inline=sent_message.message_id)
        await state.set_state(env.State.confirm_delete_book)
    elif field == "cancel":
        await callback.message.answer(_("cancel"))
        if action == "edit_book":
            await h_start.MainMenu(state, pool, bot, event_chat, event_from_user)
        else:
            await h_brief.AskForBriefReaction(callback.message, state, pool, bot, event_chat)
    elif field == "save_changes":
        await book.SaveBookToDatabase(state, pool, bot, event_from_user)
        await callback.message.answer((_("{bookid}_updated")).format(bookid=data["book_id"]))
        await h_start.MainMenu(state, pool, bot, event_chat, event_from_user)
    elif (field == "favorites") or (field == "likes"):
        # Inverse boolean field value
        old_value = data[field]
        new_value = not old_value
        book_dict = {}
        book_dict[field] = new_value
        await state.update_data(**book_dict)
        # Update the book information
        if action == "edit_book":
            # Return to field selection
            sent_message = await book.PrintBook(callback.message, state, pool, bot)
            await SelectField(sent_message, state, pool, bot, event_chat)
        else:
            await h_brief.AskForBriefReaction(callback.message, state, pool, bot, event_chat)
    else:
        # Print current value of selected field
        await state.update_data(field=field)
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
    action = data.get("action")
    value = message.text
    book_dict = {}
    book_dict[field] = value
    # Moify the book information in the user's state
    await state.update_data(**book_dict)
    # Get like to user's input
    await bot.set_message_reaction(chat_id=message.chat.id,
                                    message_id=message.message_id,
                                    reaction=[ReactionTypeEmoji(emoji='👍')])
    if action == "edit_book":
        # Return to field selection
        sent_message = await book.PrintBook(message, state, pool, bot)
        await SelectField(sent_message, state, pool, bot, event_chat)
    else:
        await h_brief.AskForBriefReaction(message, state, pool, bot, event_chat)

# -------------------------------------------------------
# Handler for edit buttons of books
@eng.base_router.callback_query(env.EditBook.filter())
async def edit_book_callback(callback: CallbackQuery, callback_data: env.EditBook, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    await state.update_data(action="edit_book")
    book_id = callback_data.book_id
    # Fetch book information from the database
    async with pool.acquire() as connection:
        row = await connection.fetchrow("""
            SELECT *
            FROM books
            WHERE user_id = $1 AND book_id = $2
        """, event_from_user.id, book_id)
    if row:
        # Store book information in the state
        book_dict = {}
        for field in env.PUBLIC_BOOK_FIELDS + env.HIDDEN_BOOK_FIELDS:
            book_dict[field] = row.get(field)
        await state.update_data(**book_dict)
        await state.update_data(book_id=book_id)
        sent_message = await book.PrintBook(callback.message, state, pool, bot)
        await SelectField(sent_message, state, pool, bot, event_chat)
    else:
        await callback.message.answer(_("book_not_found"))

# -------------------------------------------------------
# Handler for confirm delete button
@eng.base_router.callback_query(env.ConfirmDelete.filter(F.action == "delete"))
async def confirm_delete_callback(callback: CallbackQuery, callback_data: env.ConfirmDelete, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    await eng.RemoveInlineKeyboards(callback, state, bot, event_chat)
    data = await state.get_data()
    book_id = data.get("book_id")
    # Delete the book from the database
    async with pool.acquire() as connection:
        await connection.execute("""
            DELETE FROM books
            WHERE user_id = $1 AND book_id = $2
        """, event_from_user.id, book_id)
    await callback.message.answer((_("{bookid}_deleted")).format(bookid=data["book_id"]))
    # Return to main menu
    await h_start.MainMenu(state, pool, bot, event_chat, event_from_user)

# -------------------------------------------------------
# Handler for cancel delete button
@eng.base_router.callback_query(env.ConfirmDelete.filter(F.action == "cancel"))
async def cancel_delete_callback(callback: CallbackQuery, callback_data: env.ConfirmDelete, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    await eng.RemoveInlineKeyboards(callback, state, bot, event_chat)
    await callback.message.answer(_("cancel"))
    # Return to editing field selection
    await SelectField(callback.message, state, pool, bot, event_chat)