# Module for handling bot messages related to select cathegories

from email.mime import message
from modules.imports import asyncpg, _, Bot, F, Chat, User, Message, InlineKeyboardBuilder, CallbackQuery, FSMContext, env, eng
import modules.h_start as h_start # For handling start command
import modules.h_cover as h_cover # For do book cover photos
import modules.book as book # For generating list of the books
import modules.h_edit as h_edit # For handling book editing

# -------------------------------------------------------
# Prepares and sends the inline keyboard for selecting a category.
async def SelectCategory(state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    # Flush previously selected category
    await state.update_data(category=None)
    # Get the action from the state data
    data = await state.get_data()
    action = data.get("action")
    # Create new inline keyboard
    builder = InlineKeyboardBuilder()
    # Select cathegories from the database
    async with pool.acquire() as conn:
        # Fetching cathegories from the database: selects the category and counts the number of books in each category for the user
        result = await conn.fetch("""
            SELECT b.category, COUNT(*) as book_count
            FROM books b
            WHERE b.user_id = $1
            GROUP BY b.category
            ORDER BY b.category ASC
        """, event_from_user.id)
        # If there are cathegories, create buttons for each one and ask user
        if result:
            if action == "add_book":
                text = _("select_or_enter_category_add_book")
            elif action == "select_category":
                text = _("select_category_to_view_books")
            elif action == "rename_category":
                text = _("select_category_to_rename")
            elif action == "edit_book":
                text = _("select_category_to_move_book")
            for row in result:
                builder.button(text=f"{row[0]}  ({row[1]})", callback_data=env.Category(name=row[0]) )
            builder.adjust(1)
            sent_message = await bot.send_message(event_chat.id, text, reply_markup=builder.as_markup())
            await state.update_data(inline=sent_message.message_id)
        else:
            # If there are no cathegories, check if the user can add a new one
            if action == "add_book":
                await bot.send_message(event_chat.id, _("enter_category_add_book"))
            else:
                await bot.send_message(event_chat.id, _("no_books"))
                await h_start.MainMenu(state, pool, bot, event_chat)
                await state.set_state(env.State.wait_for_command)
                return
        await state.set_state(env.State.select_category)

# -------------------------------------------------------
# Handler for inline button selection of a category
@eng.base_router.callback_query(env.Category.filter())
async def category_selected(callback: CallbackQuery, callback_data: env.Category, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    await eng.RemoveInlineKeyboards(callback, state, bot, event_chat)
    await DoCategory(callback_data.name, callback.message, state, pool, bot, event_chat, event_from_user)

# -------------------------------------------------------
# Handler for entered text when the user can add a new category
@eng.base_router.message(env.State.select_category, F.text)
async def category_entered(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    data = await state.get_data()
    action = data.get("action")
    if (action == "add_book") or (action == "edit_book"):
        if len(message.text.encode()) < eng.MaxBytesInCategoryName:
            await DoCategory(message.text, message, state, pool, bot, event_chat, event_from_user)
        else:
            await message.delete()
            await message.answer(_("category_name_too_long"))
    else:
        await message.delete()
        await message.answer(_("can_not_add_category"))

# -------------------------------------------------------
# Process the selected category
async def DoCategory(category: str, message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    # Save selected category
    await state.update_data(category=category)
    # Notify the user about the selected category
    await message.answer(_("{category}_selected").format(category=category))
    # Perform the action based on the selected category
    data = await state.get_data()
    action = data.get("action")
    if action == "add_book":
        await h_cover.AskForCover(state, pool, bot, event_chat)
    elif action == "select_category":
        # Prepare the query to search for books by category
        query = """
        SELECT book_id, title, authors, year, cover_filename, category
        FROM books
        WHERE user_id=$1 AND category=$2
        ORDER BY category ASC, book_id ASC;
        """
        # Run the query to search for books in the database
        rows = await pool.fetch(query, event_from_user.id, category)
        await book.PrintBooksList(rows, message, bot, event_from_user)
        # Send main menu to the user
        await h_start.MainMenu(state, pool, bot, event_chat)
    elif action == "rename_category":
        await message.answer(_("enter_category_name"))
        await state.set_state(env.State.wait_for_new_category_name)
    elif action == "edit_book":
        # Return to editing book after category selection
        sent_message = await book.PrintBook(message, state, pool, bot)
        await h_edit.SelectField(sent_message, state, pool, bot, event_chat)

# -------------------------------------------------------
# Handler for entered text when the user enters new category name
@eng.base_router.message(env.State.wait_for_new_category_name, F.text)
async def new_cat_name_entered(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    # Check the length of the new category name
    if len(message.text.encode()) < eng.MaxBytesInCategoryName:
        # Extract information about field editing
        data = await state.get_data()
        old_cat = data.get("category")
        new_cat = message.text
        # Rename category in the database
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE books
                SET category = $1
                WHERE user_id = $2 AND category = $3
            """, new_cat, event_from_user.id, old_cat)
        # Acknowledge the renaming
        await message.answer(_("category_renamed"))
        # Return to the main menu
        await h_start.MainMenu(state, pool, bot, event_chat)
    else:
        await message.delete()
        await message.answer(_("category_name_too_long"))