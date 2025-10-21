# Module for get and put books to database

from modules.imports import asyncpg, random, _, as_list, as_key_value, env, eng
from modules.imports import Bot, Chat, User, Message, InlineKeyboardBuilder, FSMContext

# -------------------------------------------------------
# Send a brief statistic about the user's library
async def BriefStatistic(pool: asyncpg.Pool, bot: Bot, event_from_user: User, event_chat: Chat) -> None:
    async with pool.acquire() as conn:
        result = await conn.fetchval("""SELECT count(*) FROM books WHERE "user_id"=$1""", event_from_user.id)
    if (result is None) or (result == 0):
        await bot.send_message(event_chat.id, _("no_books"))
    else:
        await bot.send_message(event_chat.id, _("{result}_book","{result}_books",result).format(result=result))

# -------------------------------------------------------
# Send to user current book information from user's data and return Message object
async def PrintBook(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> Message:
    # Get the book data from the state
    data = await state.get_data() # Get stored user's data
    items = []
    # Loop through the book fields and add them to the items list
    for field in ["book_id"] + env.BOOK_FIELDS + ["category"]:
        if field in data:
            value = data[field]
            if value:
                items.append(as_key_value(_(field), value))
    content = as_list(*items)
    # Send the message with the book information and the keyboard
    sent_message = await message.answer(**content.as_kwargs())
    return sent_message

# -------------------------------------------------------
# Save book to database
async def SaveBookToDatabase(state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_from_user: User) -> None:
    # Get stored user's data
    data = await state.get_data()
    data["user_id"] = event_from_user.id
    # Build book dictionary
    fields = env.BOOK_FIELDS + env.ADVANCED_BOOK_FIELDS + env.SPECIAL_BOOK_FIELDS
    for field in fields:
        if field not in data:
            data[field] = None
    if data["book_id"]: # If book_id is already set, we are updating existing book
        book_id = data["book_id"]
        # Update the book data in the database
        async with pool.acquire() as connection:
            await connection.execute(
                f"UPDATE books SET {', '.join([f'{field} = ${i + 2}' for i, field in enumerate(fields)])} WHERE user_id = $1 AND book_id = ${len(fields) + 2}",
                event_from_user.id,
                *[data[field] for field in fields],
                book_id
            )
    else:
        # Select max book_id of current user from the database
        async with pool.acquire() as connection:
            result = await connection.fetchval("SELECT COALESCE(MAX(book_id),0) FROM books WHERE user_id = $1", event_from_user.id)
            book_id = result + 1 # Increment the max book_id by 1
        # Add manual fields
        data["book_id"] = book_id # Add book ID to the book data
        await state.update_data(book_id=book_id) # Save book ID in the state
        # Insert the book data into the database
        async with pool.acquire() as connection:
            await connection.execute(
                f"INSERT INTO books ({', '.join(fields)}) VALUES ({', '.join(['$' + str(i + 1) for i in range(len(fields))])})",
                *[data[field] for field in fields]
            )

# -------------------------------------------------------
# Loop through books dataset and send to user the books list
async def PrintBooksList(rows: list, message: Message, state: FSMContext, bot: Bot, event_from_user: User) -> None:
    # For short list of the books:
    if len(rows) == 0:
        await message.answer(_("no_books_found"))
    elif len(rows) < 10:
        await message.answer(_("{books}_found","{books}_founds",len(rows)).format(books=len(rows)))
        # Send one message for each book with title, authors, year and cover photo
        prev_category = None
        for row in rows:
            book_id = row.get("book_id")
            title = row.get("title")
            authors = row.get("authors")
            year = row.get("year")
            photo = row.get("cover_filename")  # Adjust field name as needed
            category = row.get("category")
            if category != prev_category:
                await message.answer(_("category")+": <b>"+category+"</b>", parse_mode="HTML")
                prev_category = category
            builder = InlineKeyboardBuilder()
            builder.button(text=_("edit"), callback_data=env.EditBook(book_id=book_id))
            builder.adjust(1)
            if photo:
                photo_url = eng.AWS_EXTERNAL_URL + "/" + photo
                sent_message = await message.answer_photo(photo=photo_url, caption=f"{book_id}. <b>{title}</b> - {authors}, {year}", parse_mode="HTML", reply_markup=builder.as_markup())
            else:
                sent_message = await message.answer(f"{book_id}. <b>{title}</b> - {authors}, {year}", parse_mode="HTML", reply_markup=builder.as_markup())
            await state.update_data(inline=sent_message.message_id)
    else:
        # Send one message for all books with HTML formatting
        message_text = _("{books}_found","{books}_founds",len(rows)).format(books=len(rows))+"\n"
        prev_category = None
        for row in rows:
            book_id = row.get("book_id")
            title = row.get("title")
            authors = row.get("authors")
            year = row.get("year")
            category = row.get("category")
            emoji = random.choice(["📕", "📘", "📗", "📙"])
            if category != prev_category:
                message_text += _("category")+": <b>"+category+"</b>\n"
                prev_category = category
            message_text += f"{emoji} {book_id}. <b>{title}</b> - {authors}, {year}\n"
        await message.answer(message_text, parse_mode="HTML")
