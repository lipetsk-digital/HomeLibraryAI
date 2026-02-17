# Handlers for main menu commands and inline buttons

import logging # For logging
import modules.engine as eng # For crossplatform bot engine functions and definitions
from modules.engine import _  # For internationalization and localization
import modules.actions as act # For bot commands and actions
import modules.environment as env # For bot states and callback data factories
import modules.database as db # For database functions and definitions
import modules.book as book # For book routines

'''
import modules.h_cat as h_cat # For category selection routines
import modules.h_search as h_search # For books search routines
import modules.h_lang as h_lang # For language selection routines
'''

# -------------------------------------------------------
# Handler for main menu commands
for command in act.MAIN_MENU_ACTIONS + act.ADVANCED_ACTIONS:
    @eng.on_message(eng.first_router, eng.Command(command))
    @eng.message_handler
    async def mainmenu_command(message: eng.Message, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User):
        action = message.text.split()[0].lstrip('/')
        await RunMainMenuAction(action, state, event_chat, event_from_user)

# -------------------------------------------------------
# Handler for main menu inline buttons
@eng.on_callback(eng.first_router, env.MainMenu.filter())
@eng.callback_handler
async def mainmenu_callback(message: eng.Message, callback: eng.CallbackData, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User):
    action = callback.action
    await RunMainMenuAction(action, state, event_chat, event_from_user)

# -------------------------------------------------------
# Run main menu action
async def RunMainMenuAction(action: str, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:
    await eng.send_message(chat_id=event_chat.id, text=f"You pressed a button with data: {action}")
    '''
    if action == "add":
        await state.update_data(action="add_book")
        await h_cat.SelectCategory(state, pool, bot, event_chat, event_from_user)
    elif action == "search":
        builder = InlineKeyboardBuilder()
        for action in env.SEARCH_ACTIONS:
            builder.button(text=_(action), callback_data=env.SearchMenu(action=action) )
        builder.adjust(2, 2, 1)
        message = await bot.send_message(event_chat.id, _("enter_search_query"), reply_markup=builder.as_markup())
        await state.update_data(inline=message.message_id)
        await state.update_data(action="search")
        await state.set_state(env.State.wait_for_search_query)
    elif action == "rename":
        await state.update_data(action="rename_category")
        await h_cat.SelectCategory(state, pool, bot, event_chat, event_from_user)
    elif action == "export":
        await book.ExportBooks(state, pool, bot, event_chat, event_from_user)
    elif action == "settings":
        await state.update_data(action="select_language")
        await h_lang.SelectLanguage(state, pool, bot, event_chat, event_from_user)
    '''