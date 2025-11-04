# Module for handling bot messages related to search a book

from modules.imports import asyncpg, _, Locale, Bot, F, Chat, User, Message, CallbackQuery, FSMContext, env, eng
import modules.h_start as h_start # For handling start command
import modules.book as book # For generating list of the books
import modules.h_cat as h_cat # For handling category selection

# -------------------------------------------------------
# Handler for inline button "recent books"3
@eng.base_router.callback_query(env.SearchMenu.filter(F.action == "recent"))
async def recent_books(callback: CallbackQuery, callback_data: env.SearchMenu, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    # Put preparations messages
    await eng.RemoveInlineKeyboards(callback, state, bot, event_chat)
    await book.BriefStatistic(pool, bot, event_from_user, event_chat)
    message = await bot.send_message(event_chat.id, _("recent_books"))

    # Prepare the query to search for books by title using full-text search
    query = """
    SELECT book_id, title, authors, year, cover_filename, category
    FROM books
    WHERE user_id = $1
    ORDER BY book_id DESC
    LIMIT $2;
    """
    # Run the query to search for books in the database
    rows = await pool.fetch(query, event_from_user.id, eng.CountOfRecentBooks)
    rows.reverse() # Reverse the rows order
    await book.PrintBooksList(rows, message, state, bot, event_from_user)

    # Send main menu to the user
    await h_start.MainMenu(state, pool, bot, event_chat, event_from_user)

# -------------------------------------------------------
# Handler for inline button "search by category"
@eng.base_router.callback_query(env.SearchMenu.filter(F.action == "cat"))
async def view_cat(callback: CallbackQuery, callback_data: env.SearchMenu, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    await eng.RemoveInlineKeyboards(callback, state, bot, event_chat)
    await book.BriefStatistic(pool, bot, event_from_user, event_chat)
    await h_cat.SelectCategory(state, pool, bot, event_chat, event_from_user)

# -------------------------------------------------------
# Handler for entered text when the user is searching for a book
@eng.base_router.message(env.State.wait_for_search_query, F.text)
async def search_query_entered(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:

    # Prepare the query to search for books by title using full-text search
    query = """
    SELECT book_id, title, authors, year, cover_filename, category
    FROM books
    WHERE user_id=$1 AND
    (
      to_tsvector($2, title) @@ plainto_tsquery($2, $3) OR
      to_tsvector($2, authors_full_names) @@ plainto_tsquery($2, $3) OR
      book_id::text = $3 OR
      isbn LIKE $3 || '%'
    )
    ORDER BY category ASC, book_id ASC;
    """
    user_id = event_from_user.id # Get the user ID from the message
    lang = (await state.get_data()).get("locale", "en") # Get the user's locale from the state, default to "en"
    locale = Locale.parse(lang) # Convert two-letter locale code to full locale name for PostgreSQL full-text search
    language = locale.get_language_name('en').lower() # Convert to lowercase for consistency
    search_text = message.text.strip()

    # Run the query to search for books in the database
    rows = await pool.fetch(query, user_id, language, search_text)
    await book.PrintBooksList(rows, message, state, bot, event_from_user)

    # Send main menu to the user
    await h_start.MainMenu(state, pool, bot, event_chat, event_from_user)

