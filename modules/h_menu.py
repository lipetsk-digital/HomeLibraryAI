# Handlers for main menu commands and inline buttons

from modules.imports import asyncpg, _, Bot, F, Chat, User, Message, Command, CallbackQuery, FSMContext, env, eng
import modules.h_cat as h_cat # For category selection routines
import modules.h_search as h_search # For books search routines

# -------------------------------------------------------
# Handler for main menu commands
@eng.first_router.message(Command(*(env.MAIN_MENU_ACTIONS+env.ADVANCED_ACTIONS)))
async def mainmenu_command(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    await eng.RemoveInlineKeyboards(None, state, bot, event_chat)
    command = message.text.split()[0].lstrip('/')
    await RunMainMenuAction(command, state, pool, bot, event_chat, event_from_user)

# -------------------------------------------------------
# Handler for main menu inline buttons
@eng.first_router.callback_query(env.MainMenu.filter())
async def mainmenu_callback(callback: CallbackQuery, callback_data: env.MainMenu, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    await eng.RemoveInlineKeyboards(callback, state, bot, event_chat)
    action = callback_data.action
    await RunMainMenuAction(action, state, pool, bot, event_chat, event_from_user)

# -------------------------------------------------------
# Run main menu action
async def RunMainMenuAction(action: str, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    if action == "add":
        await bot.send_message(event_chat.id, _("start_add_book"))
        await state.update_data(action="add_book")
        await h_cat.SelectCategory(state, pool, bot, event_chat, event_from_user)
    elif action == "search":
        await bot.send_message(event_chat.id, _("enter_search_query"))
        await state.update_data(action="search")
        await state.set_state(env.State.wait_for_search_query)
    elif action == "recent":
        message = await bot.send_message(event_chat.id, _("recent_books"))
        await state.update_data(action="recent")
        await h_search.RecentBooks(message, state, pool, bot, event_chat, event_from_user)
    elif action == "cat":
        await state.update_data(action="select_category")
        await h_cat.SelectCategory(state, pool, bot, event_chat, event_from_user)
