# Module for configuraion data, environment variables, and basic routines

import os # For environment variables
from modules.imports_tg import Router, Chat, Bot, Message, CallbackQuery, FSMContext
import modules.engine_common as engc # For common engine functions and definitions

# ========================================================
# Configuration data
# ========================================================

# Telegram bot token
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_PROXY = os.getenv("TELEGRAM_PROXY")

# ========================================================
# Environment variables
# ========================================================

i18n = None  # Placeholder for i18n instance
FSMi18n = None  # Placeholder for FSMi18n instance

first_router = Router() # Router for global commands
base_router = Router() # Router for base commands
last_router = Router() # Router for trash messages

pool = None  # Placeholder for database connection pool

# ========================================================
# Routines defenitions
# ========================================================

# -------------------------------------------------------
# Remove inline keyboard from callback message or last stored in state
async def RemoveInlineKeyboards(callback: CallbackQuery, state: FSMContext, bot: Bot, event_chat: Chat) -> None:
    if callback:
        await callback.answer()
        await callback.message.edit_reply_markup(reply_markup=None)
    else:
        data = await state.get_data()
        inline = data.get("inline")
        if inline:
            inline_list = inline if isinstance(inline, list) else [inline]
            for message_id in inline_list:
                try:
                    await bot.edit_message_reply_markup(chat_id=event_chat.id, message_id=message_id, reply_markup=None)
                except Exception as e:
                    engc.logging.error(f"Error deleting inline keyboard: {e}")
    await state.update_data(inline=None)

# -------------------------------------------------------
# Remove previous bot message in the chat
async def RemovePreviousBotMessage(state: FSMContext, bot: Bot, event_chat: Chat) -> None:
    data = await state.get_data()
    inline = data.get("inline")
    if inline:
        inline_list = inline if isinstance(inline, list) else [inline]
        for message_id in inline_list:
            try:
                await bot.delete_message(chat_id=event_chat.id, message_id=message_id)
            except Exception as e:
                engc.logging.error(f"Error deleting previous bot message: {e}")
        await state.update_data(inline=None)

# -------------------------------------------------------
# Handler for trash messages
@last_router.message()
async def trash_entered(message: Message) -> None:
    await message.delete()
