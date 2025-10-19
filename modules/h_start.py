# Module for handling bot messages related to start bot

from modules.imports import asyncpg, _, Bot, Chat, User, Message, Command, InlineKeyboardBuilder, FSMContext, env, eng
import modules.book as book # For book routines

# -------------------------------------------------------
# Handler for the /start command
@eng.first_router.message(Command("start"))
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



