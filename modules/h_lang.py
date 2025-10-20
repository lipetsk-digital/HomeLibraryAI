# Module for handling bot messages related to changing the language

from modules.imports import asyncpg, Bot, Router, F, Chat, User, FSMContext, _, Command, CallbackQuery, InlineKeyboardBuilder, Locale, env, eng
import modules.h_start as h_start # For handling start command

# Show menu for language selection
@eng.base_router.message(Command("settings"))
async def SelectLanguage(state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    await eng.RemoveInlineKeyboards(None, state, bot, event_chat.id)
    builder = InlineKeyboardBuilder()
    available_languages = sorted(eng.i18n.available_locales)
    for lang in available_languages:
        locale = Locale.parse(lang)
        english_name = locale.english_name.split(" (")[0]  # Get the English name without the region
        native_name = locale.get_language_name(locale=lang)
        builder.button(text=english_name+' / '+native_name, callback_data=env.Language(lang=lang) )
    builder.adjust(1)
    sent_message = await bot.send_message(event_chat.id, _("select_lang"), reply_markup=builder.as_markup())
    await state.update_data(inline=sent_message.message_id)
    await state.set_state(env.State.select_lang)

# Handler for the callback query when the user selects "settings" from the main menu
@eng.base_router.callback_query(env.Language.filter())
async def lang_callback(callback: CallbackQuery, callback_data: env.Language, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
    await eng.RemoveInlineKeyboards(callback, state, bot, event_chat.id)
    # Change locale
    await eng.FSMi18n.set_locale(state, callback_data.lang)
    # Get native name of selected language
    locale = Locale.parse(callback_data.lang)
    native_name = locale.get_language_name(locale=callback_data.lang)
    await bot.send_message(event_chat.id, _("{language}_selected").format(language=native_name))
    # Send the main menu again
    await h_start.MainMenu(state, pool, bot, event_chat)
