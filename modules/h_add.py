# Module for handling bot messages related to adding a new book

from modules.imports import asyncpg, _, Bot, F, Chat, User, Message, Command, CallbackQuery, FSMContext, env, eng
import modules.h_cat as h_cat # For manipulating cathegories

# -------------------------------------------------------
# Handler for the /add command
@eng.first_router.message(Command("add"))
async def add_command(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    await eng.RemoveInlineKeyboards(None, state, bot, event_chat)
    await StartAddBook(state, pool, bot, event_chat, event_from_user)

# -------------------------------------------------------
# Handler for the callback query when the user selects "add" from the main menu
@eng.first_router.callback_query(env.MainMenu.filter(F.action=="add"))
async def add_callback(callback: CallbackQuery, callback_data: env.MainMenu, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    await eng.RemoveInlineKeyboards(callback, state, bot, event_chat)
    await StartAddBook(state, pool, bot, event_chat, event_from_user)

# -------------------------------------------------------
# Start adding a new book
async def StartAddBook(state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    message = await bot.send_message(event_chat.id, _("start_add_book"))
    await state.update_data(action="add_book")
    await h_cat.SelectCategory(message, state, pool, bot, event_chat, event_from_user)