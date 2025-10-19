# Module for handling bot messages related to start bot

from modules.imports import asyncpg, _, Bot, Chat, User, Message, Command, InlineKeyboardBuilder, FSMContext, env, eng
from aiogram.types import BotCommand, BotCommandScopeDefault # For setting bot commands
import modules.book as book # For book routines

# -------------------------------------------------------
# Prepare the bot's bottom left main menu commands
async def PrepareGlobalMenu(bot: Bot):
    # Loop through all available languages and set the bot commands for each one    
    available_languages = eng.i18n.available_locales
    eng.logging.debug(f"Available languages: {available_languages}")
    for lang in available_languages:
        commands = []
        actions = env.MAIN_MENU_ACTIONS + env.ADVANCED_ACTIONS
        for action in actions:
            commands.append(BotCommand(command=action, description=eng.i18n.gettext(action, locale=lang)))
        await bot.set_my_commands(commands, BotCommandScopeDefault(), lang)

# -------------------------------------------------------
# Handler for the /start command
@eng.base_router.message(Command("start"))
async def start_command(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO logs (user_id, nickname, username) VALUES ($1, $2, $3)",
            event_from_user.id, event_from_user.username, event_from_user.full_name
        )
    await book.BriefStatistic(pool, bot, event_from_user, event_chat)
    await MainMenu(state, pool, bot, event_chat)

# -------------------------------------------------------
# Prepare and send the main menu inline-buttons for the user
async def MainMenu(state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
    await eng.RemoveInlineKeyboards(None, state, bot, event_chat)
    builder = InlineKeyboardBuilder()
    for action in env.MAIN_MENU_ACTIONS:
        builder.button(text=_(action), callback_data=env.MainMenu(action=action) )
    builder.adjust(2, 2)
    message = await bot.send_message(event_chat.id, _("main_menu"), reply_markup=builder.as_markup())
    await state.update_data(inline=message.message_id)
    await state.set_state(env.State.wait_for_command)



