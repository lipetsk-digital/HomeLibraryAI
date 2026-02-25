# Module for handling bot messages related to search a book

import modules.engine as eng # For crossplatform bot engine functions and definitions
from modules.engine import _  # For internationalization and localization
import modules.environment as env # For bot states and callback data factories
import modules.database as db # For database functions and definitions
import modules.book as book # For book routines

import modules.h_start as h_start # For handling start command
import modules.h_cat as h_cat # For handling category selection

from babel import Locale

# -------------------------------------------------------
# Constants

CountOfRecentBooks = 5 # Number of recent books to show in "recent books" search

# -------------------------------------------------------
# Handler for inline button "cancel"
@eng.on_callback(eng.base_router,env.SearchMenu.filter(eng.F.action == "cancel"))
@eng.callback_handler
async def search_cancel(message: eng.Message, callback: eng.CallbackData, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:
    await h_start.MainMenu(state, event_chat, event_from_user)

# -------------------------------------------------------
# Handler for inline button "search by category"
@eng.on_callback(eng.base_router,env.SearchMenu.filter(eng.F.action == "cat"))
@eng.callback_handler
async def view_cat(message: eng.Message, callback: eng.CallbackData, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:
    await h_cat.SelectCategory(state, event_chat, event_from_user)

# -------------------------------------------------------
# Handler for inline buttons "recent books", "favorite books", "liked books"
@eng.on_callback(eng.base_router,env.SearchMenu.filter())
@eng.callback_handler
async def recent_books(message: eng.Message, callback: eng.CallbackData, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:
    await DoSearch(callback.action, "", state, event_chat, event_from_user)

# -------------------------------------------------------
# Handler for entered text when the user is searching for a book
@eng.on_message(eng.base_router, env.State.wait_for_command, eng.F.text)
@eng.on_message(eng.base_router, env.State.wait_for_search_query, eng.F.text)
@eng.message_handler
async def search_query_entered(message: eng.Message, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:
    await DoSearch("text", message.text, state, event_chat, event_from_user)

# -------------------------------------------------------
async def DoSearch(action: str, text: str, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:

    await eng.send_message(event_chat.id, _(action + "_intro"))

    # Prepare the query
    async with db.pool.acquire() as conn:
        query = """
        SELECT book_id, title, authors, year, cover_filename, cover_token, category, favorites, likes
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
            rows = await conn.fetch(query, event_from_user.id, CountOfRecentBooks)
            rows.reverse() # Reverse the rows order

        # Print the books list
        await book.PrintBooksList(rows, state, event_chat, event_from_user)
        
    # Send main menu to the user
    await h_start.MainMenu(state, event_chat, event_from_user)
