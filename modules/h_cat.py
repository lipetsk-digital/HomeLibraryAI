# Module for handling bot messages related to select cathegories

import modules.engine as eng # For crossplatform bot engine functions and definitions
from modules.engine import _  # For internationalization and localization
import modules.actions as act # For bot commands and actions
import modules.environment as env # For bot states and callback data factories
import modules.database as db # For database functions and definitions
import modules.book as book # For book routines

import modules.h_start as h_start # For handling start command
import modules.h_search as h_search # For handling book search routines
import modules.h_cover as h_cover # For do book cover photos
#import modules.h_edit as h_edit # For handling book editing

from email.mime import message

# -------------------------------------------------------
# Prepares and sends the inline keyboard for selecting a category.
async def SelectCategory(state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:
    # Flush previously selected category
    await state.update_data(category=None)
    # Get the action from the state data
    data = await state.get_data()
    action = data.get("action")
    # Select cathegories from the database
    async with db.pool.acquire() as conn:
        # Fetching cathegories from the database: selects the category and counts the number of books in each category for the user
        result = await conn.fetch("""
            SELECT b.category, COUNT(*) as book_count
            FROM books b
            WHERE b.user_id = $1
            GROUP BY b.category
            ORDER BY b.category ASC
        """, event_from_user.id)
        # If there are cathegories, create buttons for each one and ask user
        if result:
            # Create new inline keyboard
            keyboard = []
            buttons_count = 0
            # Prepare text header based on the action
            if action == "add_book":
                text = _("select_or_enter_category_add_book")
            elif action == "search":
                text = _("select_category_to_view_books")
            elif action == "rename_category":
                text = _("select_category_to_rename")
            elif action == "edit_book":
                text = _("select_category_to_move_book")
            for row in result:
                keyboard.append(eng.CallbackButton(text=f"{row[0]}  ({row[1]})", payload=env.Category(name=row[0])))
                buttons_count += 1
                if  buttons_count >= eng.MaxButtonsInMessage:
                    sent_message = await eng.send_message(event_chat.id, text)
                    await eng.send_inline_keyboard(sent_message, keyboard, state)
                    buttons_count = 0
                    keyboard = []
                    text = _("continue_selecting_category")
            keyboard.append(eng.CallbackButton(text=_("cancel"), payload=env.Category(name="cancel")))
            sent_message = await eng.send_message(event_chat.id, text)
            await eng.send_inline_keyboard(sent_message, keyboard, state)
        else:
            # If there are no cathegories, check if the user can add a new one
            if action == "add_book":
                await eng.send_message(event_chat.id, _("enter_category_add_book"))
            else:
                await eng.send_message(event_chat.id, _("no_books"))
                await h_start.MainMenu(state, event_chat, event_from_user)
                return
        await state.set_state(env.State.select_category)

# -------------------------------------------------------
# Handler for inline button "cancel" in category selection
@eng.on_callback(eng.base_router,env.Category.filter(eng.F.name == "cancel"))
@eng.callback_handler
async def category_selection_cancel(message: eng.Message, callback: eng.CallbackData, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:
    #await eng.RemovePreviousBotMessage(state, bot, event_chat)
    await h_start.MainMenu(state, event_chat, event_from_user)

# -------------------------------------------------------
# Handler for inline button selection of a category

@eng.on_callback(eng.base_router,env.Category.filter())
@eng.callback_handler
async def category_selected(message: eng.Message, callback: eng.CallbackData, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:
    #await engt.RemovePreviousBotMessage(state, bot, event_chat)
    await DoCategory(callback.name, state, event_chat, event_from_user)

# -------------------------------------------------------
# Handler for entered text when the user can add a new category
@eng.on_message(eng.base_router, env.State.select_category, eng.F_text())
@eng.message_handler
async def category_entered(message: eng.Message, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:
    data = await state.get_data()
    action = data.get("action")
    MaxBytesInCategoryName = eng.MaxBytesInButtonCaption-len(env.Category.prefix.encode())-1
    if (action == "add_book") or (action == "edit_book"):
        if len(message.text.encode()) < MaxBytesInCategoryName:
            if message.text.lower() == "cancel":
                await message.delete()
                await eng.send_message(event_chat.id, _("no_such_category_name"))
            else:
                await DoCategory(message.text, state, event_chat, event_from_user)
        else:
            await message.delete()
            await eng.send_message(event_chat.id, _("category_name_{size}").format(size=MaxBytesInCategoryName))
    else:
        await message.delete()
        await eng.send_message(event_chat.id, _("can_not_add_category"))

# -------------------------------------------------------
# Process the selected category
async def DoCategory(category: str, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:
    # Save selected category
    await state.update_data(category=category)
    # Perform the action based on the selected category
    data = await state.get_data()
    action = data.get("action")
    if action == "add_book":
        await eng.send_message(event_chat.id, _("adding_book_in_{category}").format(category=category))
        await h_cover.AskForCover(state, event_chat)
    elif action == "search":
        await h_search.DoSearch("cat", category, state, event_chat, event_from_user)
        pass
    '''
    elif action == "rename_category":
        await eng.send_message(event_chat.id, _("rename_category"))
        await eng.send_message(event_chat.id, category)
        await state.set_state(env.State.wait_for_new_category_name)
    elif action == "edit_book":
        # Return to editing book after category selection
        sent_message = await book.PrintBook(message, state, pool, bot)
        await h_edit.SelectField(sent_message, state, pool, bot, event_chat)
    '''

'''
# -------------------------------------------------------
# Handler for entered text when the user enters new category name
@engt.base_router.message(env.State.wait_for_new_category_name, F.text)
async def new_cat_name_entered(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    # Check the length of the new category name
    if len(message.text.encode()) < engb.MaxBytesInCategoryName:
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
            """, new_cat, event_from_user.id, old_cat)
        # Acknowledge the renaming
        await message.answer(_("category_renamed"))
        # Return to the main menu
        await h_start.MainMenu(state, pool, bot, event_chat, event_from_user)
    else:
        await message.delete()
        await message.answer(_("category_name_{size}").format(size=engb.MaxBytesInCategoryName))
'''