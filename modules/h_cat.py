# Module for handling bot messages related to select cathegories

from modules.imports import asyncpg, _, Bot, F, Chat, User, Message, Command, InlineKeyboardBuilder, CallbackQuery, FSMContext, env, eng
import modules.h_start as h_start # For handling start command
#import modules.h_cover as h_cover # For do book cover photos
#import modules.book as book # For generating list of the books

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
            elif action == "select_cat":
                text = _("select_category_to_view_books")
            elif action == "rename_category":
                text = _("select_category_to_rename")
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

# Handler for inline button selection of a category
@cat_router.callback_query(env.Category.filter())
async def category_selected(callback: CallbackQuery, callback_data: env.Category, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    await env.RemoveMyInlineKeyboards(callback, state)
    await DoCategory(callback_data.name, callback.message, callback.from_user.id, state, pool, bot)

# Handler for entered text when the user can add a new category
@cat_router.message(env.State.select_category, F.text)
async def category_entered(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    data = await state.get_data()
    can_add = data.get("can_add")
    if can_add:
        await DoCategory(message.text, message, message.from_user.id, state, pool, bot)
    else:
        await message.delete()
        await message.answer(_("can_not_add_category"))

# Process the selected category
async def DoCategory(category: str, message: Message, user_id: int, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    # Save selected category
    await state.update_data(category=category)
    # Notify the user about the selected category
    await message.answer(_("{category}_selected").format(category=category))
    # Retrieve the action from the state
    data = await state.get_data()
    action = data.get("action")
    # Perform the action based on the selected category
    if action == "add_book":
        await h_cover.AskForCover(message, state, pool, bot)
    elif action == "select_cat":
        # Prepare the query to search for books by title using full-text search
        query = """
        SELECT book_id, title, authors, year, cover_filename
        FROM books
        WHERE user_id=$1 AND category=$2
        ORDER BY book_id ASC;
        """
        # Run the query to search for books in the database
        rows = await pool.fetch(query, user_id, category)
        await book.PrintBooksList(rows, message, bot)
        # Send main menu to the user
        await h_start.MainMenu(message, state, pool, bot)
    elif action == "rename_category":
        await message.answer(_("enter_category_name"))
        await state.set_state(env.State.wait_for_new_category_name)

# Handler for the /cat command
@eng.first_router.message(Command("cat"))
async def cat_command(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    await eng.RemoveInlineKeyboards(None, state, bot, event_chat)
    await SelectCategoryToViewBooks(state, pool, bot, event_chat, event_from_user)

# Handler for the callback query when the user selects "cat" from the main menu
@eng.first_router.callback_query(env.MainMenu.filter(F.action=="cat"))
async def cat_callback(callback: CallbackQuery, callback_data: env.MainMenu, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    await env.RemoveMyInlineKeyboards(callback, state, bot, event_chat)
    await SelectCategoryToViewBooks(state, pool, bot, event_chat, event_from_user)

# Start selecting category to view books
async def SelectCategoryToViewBooks(state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    await state.update_data(action="select_cat")
    await SelectCategory(state, pool, bot, event_chat, event_from_user)