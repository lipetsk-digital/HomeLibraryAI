# Module for handling bot messages related to start bot

import logging # For logging

import modules.engine as eng # For crossplatform bot engine functions and definitions
import modules.actions as act # For bot commands and actions
import modules.database as db # For database functions and definitions
#import modules.book as book # For book routines

@eng.on_start_conversation(eng.first_router)
@eng.message_handler
async def IntroMessage(message: eng.Message, callback, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User):
    logging.info(f"User {event_from_user.id} started a conversation with the bot")
    await eng.bot.send_message(chat_id = event_chat.id, text = "This is a placeholder for the intro message.")
    async with db.pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO logs (user_id, nickname, username) VALUES ($1, $2, $3)",
            event_from_user.id, event_from_user.username, event_from_user.full_name
        )
    #await MainMenu(state, pool, bot, event_chat, event_from_user)

@eng.on_message(eng.base_router)
@eng.message_handler
async def Echo(message: eng.Message, callback, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User):
    data = await state.get_data()
    await state.update_data(last_message=message.text)
    await eng.bot.send_message(chat_id = event_chat.id, text = f"You say: {data.get('last_message', '')} -> {message.text}")

'''
async def PrepareGlobalMenu(bot: Bot_tg) -> None:
    """ Prepare the bot's bottom left main menu commands, telegram only.
    
     Args:
        bot (Bot_tg): The telegram bot instance. Assigned automatically by dispatcher's startup event."""
    # Loop through all available languages and set the bot commands for each one    
    available_languages = eng.i18n.available_locales
    logging.debug(f"Available languages: {available_languages}")
    for lang in available_languages:
        commands = []
        actions = act.MAIN_MENU_ACTIONS + act.ADVANCED_ACTIONS
        for action in actions:
            commands.append(BotCommand_tg(command=action, description=eng.i18n.gettext(action, locale=lang)))
        await bot.set_my_commands(commands, BotCommandScopeDefault_tg(), lang)
'''
'''
# -------------------------------------------------------
# Handler for the /start command
@eng.command(eng.first_router, "start")
async def start_command(message, state, pool, bot, event_chat, event_from_user):
    logging.debug("Start command received")
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO logs (user_id, nickname, username) VALUES ($1, $2, $3)",
            event_from_user.id, event_from_user.username, event_from_user.full_name
        )
    await MainMenu(state, pool, bot, event_chat, event_from_user)
    '''

'''
# -------------------------------------------------------
# Prepare and send the main menu inline-buttons for the user
async def MainMenu(state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    await engt.RemovePreviousBotMessage(state, bot, event_chat)
    message = await book.BriefStatistic(pool, bot, event_from_user, event_chat)
    builder = InlineKeyboardBuilder()
    for action in env.MAIN_MENU_ACTIONS:
        builder.button(text=_(action), callback_data=env.MainMenu(action=action) )
    builder.adjust(2, 2)
    await message.edit_reply_markup(reply_markup=builder.as_markup())
    await state.update_data(inline=message.message_id)
    await state.set_state(env.State.wait_for_command)
'''


