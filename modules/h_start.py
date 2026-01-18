# Module for handling bot messages related to start bot

import logging # For logging

import modules.engine as eng # For crossplatform bot engine functions and definitions
from modules.engine import _  # For internationalization and localization
import modules.actions as act # For bot commands and actions
import modules.database as db # For database functions and definitions
import modules.book as book # For book routines

# -------------------------------------------------------
# Handler for the /start command
@eng.on_start_conversation(eng.first_router)
@eng.message_handler
async def WelcomeMessage(message: eng.Message, callback, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User):
    logging.info(f"User {event_from_user.id} started a conversation with the bot")
    await eng.bot.send_message(chat_id = event_chat.id, text = _("welcome_message"))
    async with db.pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO logs (platform, user_id, nickname, username) VALUES ($1, $2, $3, $4)",
            eng.MESSENGER, event_from_user.id, event_from_user.username, event_from_user.first_name+" "+event_from_user.last_name
        )
    await MainMenu(state, event_chat, event_from_user)

# -------------------------------------------------------
# Test echo handler
@eng.on_message(eng.base_router)
@eng.message_handler
async def Echo(message: eng.Message, callback, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User):
    data = await state.get_data()
    await state.update_data(last_message=message.text)
    await eng.bot.send_message(chat_id = event_chat.id, text = f"You say: {data.get('last_message', '')} -> {message.text}")

# -------------------------------------------------------
# Prepare and send the main menu inline-buttons for the user
async def MainMenu(state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:
    #await engt.RemovePreviousBotMessage(state, bot, event_chat)
    message = await book.BriefStatistic(event_from_user, event_chat)
    #builder = InlineKeyboardBuilder()
    #for action in env.MAIN_MENU_ACTIONS:
    #    builder.button(text=_(action), callback_data=env.MainMenu(action=action) )
    #builder.adjust(2, 2)
    #await message.edit_reply_markup(reply_markup=builder.as_markup())
    #await state.update_data(inline=message.message_id)
    #await state.set_state(env.State.wait_for_command)
