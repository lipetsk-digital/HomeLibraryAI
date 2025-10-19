# Module for handling bot messages related to start bot

from imports import asyncpg, Bot, Chat, User, FSMContext, _, Command, InlineKeyboardBuilder, eng, env
import modules.book as book # For book routines

# Handler for the /start command
@env.first_router.message(Command("start"))
async def start_command(state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_from_user: User, event_chat: Chat) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO logs (user_id, nickname, username) VALUES ($1, $2, $3)",
            event_from_user.id, event_from_user.username, event_from_user.full_name
        )
    await book.BriefStatistic(pool=pool, bot=bot, event_from_user=event_from_user, event_chat=event_chat)
    await MainMenu(state, pool, bot)

# Prepare and send the main menu inline-buttons for the user
async def MainMenu(state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
    await eng.RemoveInlineKeyboards(state=state, bot=bot, event_chat=event_chat)
    builder = InlineKeyboardBuilder()
    for action in env.MAIN_MENU_ACTIONS:
        builder.button(text=_(action), callback_data=env.MainMenu(action=action) )
    builder.adjust(2, 2)
    sent_message = await bot.send_message(event_chat.id, _("main_menu"), reply_markup=builder.as_markup())
    await state.update_data(inline=sent_message.message_id)
    await state.set_state(env.State.wait_for_command)



