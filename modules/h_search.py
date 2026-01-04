# Module for handling bot messages related to search a book

from modules.imports import asyncpg, _, Locale, Bot, F, Chat, User, Message, CallbackQuery, FSMContext, env, eng
import modules.h_start as h_start # For handling start command
import modules.book as book # For generating list of the books
import modules.h_cat as h_cat # For handling category selection

# -------------------------------------------------------
# Handler for inline button "cancel"
@eng.base_router.callback_query(env.SearchMenu.filter(F.action == "cancel"))
async def search_cancel(callback: CallbackQuery, callback_data: env.SearchMenu, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    await eng.RemovePreviousBotMessage(state, bot, event_chat)
    await h_start.MainMenu(state, pool, bot, event_chat, event_from_user)

# -------------------------------------------------------
# Handler for inline button "search by category"
@eng.base_router.callback_query(env.SearchMenu.filter(F.action == "cat"))
async def view_cat(callback: CallbackQuery, callback_data: env.SearchMenu, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    await eng.RemovePreviousBotMessage(state, bot, event_chat)
    await h_cat.SelectCategory(state, pool, bot, event_chat, event_from_user)

# -------------------------------------------------------
# Handler for inline buttons "recent books", "favorite books", "liked books"
@eng.base_router.callback_query(env.SearchMenu.filter())
async def recent_books(callback: CallbackQuery, callback_data: env.SearchMenu, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    await eng.RemovePreviousBotMessage(state, bot, event_chat)
    await DoSearch(callback_data.action, "", state, pool, bot, event_chat, event_from_user)

# -------------------------------------------------------
# Handler for entered text when the user is searching for a book
@eng.first_router.message(env.State.wait_for_command, F.text) # Also in main menu state
@eng.base_router.message(env.State.wait_for_search_query, F.text)
async def search_query_entered(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    await eng.RemovePreviousBotMessage(state, bot, event_chat)
    await DoSearch("text", message.text, state, pool, bot, event_chat, event_from_user)

# -------------------------------------------------------
async def DoSearch(action: str, text: str, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:

    await bot.send_message(event_chat.id, _(action + "_intro"))

    # Prepare the query
    async with pool.acquire() as conn:
        query = """
        SELECT book_id, title, authors, year, cover_filename, category, favorites, likes
        FROM books
        WHERE user_id = $1
        """
        if action == "text":
            query += """
            AND
            (
                to_tsvector($2, title) @@ plainto_tsquery($2, $3) OR
                to_tsvector($2, authors_full_names) @@ plainto_tsquery($2, $3) OR
                book_id::text = $3 OR
                isbn LIKE $3 || '%'
            )
            ORDER BY category ASC, book_id ASC
            """
            lang = (await state.get_data()).get("locale", "en") # Get the user's locale from the state, default to "en"
            locale = Locale.parse(lang) # Convert two-letter locale code to full locale name for PostgreSQL full-text search
            language = locale.get_language_name('en').lower() # Convert to lowercase for consistency
            search_text = text.strip()
            rows = await conn.fetch(query, event_from_user.id, language, search_text)

        elif action == "cat":
            query += """
                AND category = $2
                ORDER BY category ASC, book_id ASC
            """
            rows = await conn.fetch(query, event_from_user.id, text)

        elif action == "favorites":
            query += """
                AND favorites = TRUE
                ORDER BY category ASC, book_id ASC
            """
            rows = await conn.fetch(query, event_from_user.id)

        elif action == "likes":
            query += """
                AND likes = TRUE
                ORDER BY category ASC, book_id ASC
            """
            rows = await conn.fetch(query, event_from_user.id)

        elif action == "recent":
            query += """
                ORDER BY book_id DESC 
                LIMIT $2
            """
            rows = await conn.fetch(query, event_from_user.id, eng.CountOfRecentBooks)
            rows.reverse() # Reverse the rows order

        # Print the books list
        await book.PrintBooksList(rows, state, bot, event_chat, event_from_user)
        
    # Send main menu to the user
    await h_start.MainMenu(state, pool, bot, event_chat, event_from_user)
