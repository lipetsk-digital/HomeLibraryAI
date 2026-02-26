# Module for handling bot messages related to changing the language

import modules.engine as eng # For crossplatform bot engine functions and definitions
from modules.engine import _  # For internationalization and localization
import modules.environment as env # For bot states and callback data factories

import modules.h_start as h_start # For handling start command

from babel import Locale # For locale handling

# Show menu for language selection
@eng.on_message(eng.first_router, eng.Command("settings"))
@eng.message_handler
async def SelectLanguage(message: eng.Message, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:
    keyboard = []
    try:
        available_languages = sorted(eng.i18n.available_locales)
    except:
        available_languages = ['ru']
    for lang in available_languages:
        locale = Locale.parse(lang)
        english_name = locale.english_name.split(" (")[0]  # Get the English name without the region
        native_name = locale.get_language_name(locale=lang)
        keyboard.append(eng.CallbackButton(text=english_name+' / '+native_name, payload=env.Language(lang=lang) ))
    sent_message = await eng.send_message(event_chat.id, _("select_lang"))
    await eng.send_inline_keyboard(sent_message, keyboard, state)
    await state.set_state(env.State.select_lang)

# Handler for the callback query when the user selects "settings" from the main menu
@eng.on_callback(eng.base_router, env.Language.filter())
@eng.callback_handler
async def lang_callback(message: eng.Message, callback: eng.CallbackData, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:
    # Change locale
    try:
        await eng.FSMi18n.set_locale(state, callback.lang)
        # Get native name of selected language
        locale = Locale.parse(callback.lang)
        native_name = locale.get_language_name(locale=callback.lang)
        await eng.send_message(event_chat.id, _("{language}_selected").format(language=native_name))
    finally:
        # Send the main menu again
        await h_start.MainMenu(state, event_chat, event_from_user)
