# Module for handling bot messages related to start bot

import logging # For logging
import modules.engine as eng # For crossplatform bot engine functions and definitions
from modules.engine import _  # For internationalization and localization
import modules.actions as act # For bot commands and actions
import modules.environment as env # For bot states and callback data factories
import modules.database as db # For database functions and definitions
import modules.book as book # For book routines

# -------------------------------------------------------
# Handler for the /start command
@eng.on_start_conversation(eng.first_router)
@eng.message_handler
async def WelcomeMessage(message: eng.Message, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User):
    logging.info(f"User {event_from_user.id} started a conversation with the bot")
    await eng.send_message(chat_id = event_chat.id, text = _("welcome_message"))
    async with db.pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO logs (platform, user_id, nickname, username) VALUES ($1, $2, $3, $4)",
            eng.MESSENGER, event_from_user.id, event_from_user.username, event_from_user.first_name+" "+event_from_user.last_name
        )
    await MainMenu(state, event_chat, event_from_user)

# -------------------------------------------------------
# Prepare and send the main menu inline-buttons for the user
async def MainMenu(state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:
    #await engt.RemovePreviousBotMessage(state, bot, event_chat)
    message = await book.BriefStatistic(event_from_user, event_chat)
    keyboard = []
    for action in act.MAIN_MENU_ACTIONS:
        keyboard.append(eng.CallbackButton(text=_(action), payload=env.MainMenu(action=action)))
    await eng.send_inline_keyboard(message, keyboard, state, 2)
    await state.set_state(env.State.wait_for_command)
