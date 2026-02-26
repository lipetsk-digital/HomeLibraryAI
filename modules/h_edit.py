# Module for edit values of book fields

import modules.engine as eng # For crossplatform bot engine functions and definitions
from modules.engine import _  # For internationalization and localization
import modules.actions as act # For bot commands and actions
import modules.environment as env # For bot states and callback data factories
import modules.common as com # For common functions and definitions
import modules.database as db # For database functions and definitions
import modules.book as book # For save book to database

import modules.h_cat as h_cat # For category selection routines
import modules.h_start as h_start # For main menu routines
import modules.h_brief as h_brief # For brief routines

# -------------------------------------------------------
# Send message with inline-buttons of the book fields selection
async def SelectField(message: eng.Message, state: eng.FSMContext, event_chat: eng.Chat) -> None:
    data = await state.get_data()
    action = data.get("action")
    # Create new inline keyboard
    keyboard = []
    if action == "edit_book":
        fields = act.PUBLIC_BOOK_FIELDS + act.BOOK_ACTIONS
    else:
        fields = act.PUBLIC_BOOK_FIELDS + ["cancel"]
    for field in fields:
        keyboard.append(eng.CallbackButton(text=_(field), payload=env.BookFields(field=field)))
    # Add to the message with book information the keyboard
    sent_message = await message.reply(_("select_field"))
    await eng.send_inline_keyboard(sent_message, keyboard, state, 2, eng.onButtonClick.RemoveKeyboardKeepMessage)
    await state.set_state(env.State.select_field)

# -------------------------------------------------------
# Handle button of field selection
@eng.on_callback(eng.base_router,env.BookFields.filter())
@eng.callback_handler
async def field_selected(message: eng.Message, callback: eng.CallbackData, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:
    field = callback.field
    data = await state.get_data()
    action = data.get("action")
    # Handle special books actions
    if field == "move_book":
        await h_cat.SelectCategory(state, event_chat, event_from_user)
    elif field == "delete_book":
        keyboard = []
        for action in act.CONFIRM_DELETE:
            keyboard.append(eng.CallbackButton(text=_(action), payload=env.ConfirmDelete(action=action)))
        sent_message = await message.reply(_("confirm_delete_book"))
        await eng.send_inline_keyboard(sent_message, keyboard, state, 2, eng.onButtonClick.RemoveKeyboardKeepMessage)
        await state.set_state(env.State.confirm_delete_book)
    elif field == "cancel":
        await message.reply(_("cancel"))
        if action == "edit_book":
            await h_start.MainMenu(state, event_chat, event_from_user)
        else:
            await h_brief.AskForBriefReaction(message, state, event_chat)
    elif field == "save_changes":
        await book.SaveBookToDatabase(state, event_from_user)
        await message.reply((_("{bookid}_updated")).format(bookid=data["book_id"]))
        await h_start.MainMenu(state, event_chat, event_from_user)
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
            sent_message = await book.PrintBook(message, state)
            await SelectField(sent_message, state, event_chat)
        else:
            await h_brief.AskForBriefReaction(message, state, event_chat)
    else:
        # Print current value of selected field
        await state.update_data(field=field)
        if field in data:
            value = data[field]
            if value:
                content = "<b>" + _(field) + ":</b> " + _("edit_field_value")
                await message.reply(content, parse_mode=eng.ParseMode.HTML)
                await message.reply(value)
            else:
                content = "<b>" + _(field) + ":</b> " + _("edit_field_empty")
                await message.reply(content, parse_mode=eng.ParseMode.HTML)
        else:
            content = "<b>" + _(field) + ":</b> " + _("edit_field_empty")
            await message.reply(content, parse_mode=eng.ParseMode.HTML)
        # Wait for new value of selected field
        await state.set_state(env.State.wait_for_field_value)

# -------------------------------------------------------
# Handler for entered text when the user edits field value
@eng.on_message(eng.base_router, env.State.wait_for_field_value, eng.F_text())
@eng.message_handler
async def value_entered(message: eng.Message, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:
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
    await message.set_like()

    if action == "edit_book":
        # Return to field selection
        sent_message = await book.PrintBook(message, state)
        await SelectField(sent_message, state, event_chat)
    else:
        await h_brief.AskForBriefReaction(message, state, event_chat)

# -------------------------------------------------------
# Handler for edit buttons of books
@eng.on_callback(eng.base_router,env.EditBook.filter())
@eng.callback_handler
async def edit_book_callback(message: eng.Message, callback: eng.CallbackData, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:
    await state.update_data(action="edit_book")
    book_id = callback.book_id
    # Fetch book information from the database
    async with db.pool.acquire() as connection:
        row = await connection.fetchrow("""
            SELECT *
            FROM books
            WHERE user_id = $1 AND book_id = $2
        """, event_from_user.id, book_id)
    if row:
        # Store book information in the state
        book_dict = {}
        for field in act.PUBLIC_BOOK_FIELDS + act.HIDDEN_BOOK_FIELDS:
            if field != "platform":
                book_dict[field] = row.get(field)
        await state.update_data(**book_dict)
        await state.update_data(book_id=book_id)
        sent_message = await book.PrintBook(message, state)
        await SelectField(sent_message, state, event_chat)
    else:
        await message.reply(_("book_not_found"))

# -------------------------------------------------------
# Handler for confirm delete button
@eng.on_callback(eng.base_router,env.ConfirmDelete.filter(eng.F.action == "delete"))
@eng.callback_handler
async def confirm_delete_callback(message: eng.Message, callback: eng.CallbackData, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:
    data = await state.get_data()
    book_id = data.get("book_id")
    # Delete the book from the database
    async with db.pool.acquire() as connection:
        await connection.execute("""
            DELETE FROM books
            WHERE user_id = $1 AND book_id = $2
        """, event_from_user.id, book_id)
    await message.reply((_("{bookid}_deleted")).format(bookid=data["book_id"]))
    # Return to main menu
    await h_start.MainMenu(state, event_chat, event_from_user)

# -------------------------------------------------------
# Handler for cancel delete button
@eng.on_callback(eng.base_router,env.ConfirmDelete.filter(eng.F.action == "cancel"))
@eng.callback_handler
async def cancel_delete_callback(message: eng.Message, callback: eng.CallbackData, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:
    await message.reply(_("cancel"))
    # Return to editing field selection
    await SelectField(message, state, event_chat)