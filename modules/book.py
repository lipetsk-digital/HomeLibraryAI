# Module for get and put books to database

from modules.imports_tg import asyncpg, web, io, random, csv, json, datetime, _, as_list, as_key_value, env, engb, engw
from modules.imports_tg import Bot, Chat, User, Message, InlineKeyboardBuilder, FSMContext, BufferedInputFile
import modules.h_start as h_start # For handling start command
import modules.engine_web as engw # For basic web functions and definitions

# -------------------------------------------------------
# Send a brief statistic about the user's library
async def BriefStatistic(pool: asyncpg.Pool, bot: Bot, event_from_user: User, event_chat: Chat) -> Message:
    async with pool.acquire() as conn:
        result = await conn.fetchval("""SELECT count(*) FROM books WHERE "user_id"=$1""", event_from_user.id)
    if (result is None) or (result == 0):
        message = await bot.send_message(event_chat.id, _("no_books"))
    else:
        message = await bot.send_message(event_chat.id, _("{result}_book","{result}_books",result).format(result=result))
    return message

# -------------------------------------------------------
# Send to user current book information from user's data and return Message object
async def PrintBook(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> Message:
    # Get the book data from the state
    data = await state.get_data() # Get stored user's data
    items = []
    # Loop through the book fields and add them to the items list
    for field in ["book_id"] + env.PUBLIC_BOOK_FIELDS + ["category"]:
        if field in data:
            value = data[field]
            if value:
                if (field == "favorites") or (field == "likes"):
                    items.append(_(field))
                else:
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
    fields = env.PUBLIC_BOOK_FIELDS + env.HIDDEN_BOOK_FIELDS
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
async def PrintBooksList(rows: list, state: FSMContext, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    # For short list of the books:
    if len(rows) == 0:
        await bot.send_message(event_chat.id, _("no_books_found"))
    elif len(rows) < 10:
        await bot.send_message(event_chat.id, _("{books}_found","{books}_founds",len(rows)).format(books=len(rows)))
        # Send one message for each book with title, authors, year and cover photo
        prev_category = None
        for row in rows:
            book_id = row.get("book_id")
            title = row.get("title")
            authors = row.get("authors")
            year = row.get("year")
            photo = row.get("cover_filename")  # Adjust field name as needed
            category = row.get("category")
            favorites = " ⭐" if row.get("favorites") else ""
            likes = " 👍" if row.get("likes") else ""
            if category != prev_category:
                await bot.send_message(event_chat.id, "📂 <b>"+category+"</b>", parse_mode="HTML")
                prev_category = category
            builder = InlineKeyboardBuilder()
            builder.button(text=_("edit"), callback_data=env.EditBook(book_id=book_id))
            builder.adjust(1)
            if photo:
                photo_url = engb.AWS_EXTERNAL_URL + "/" + photo
                await bot.send_photo(event_chat.id, photo=photo_url, caption=f"{book_id}.{favorites}{likes} <b>{title}</b> - {authors}, {year}", parse_mode="HTML", reply_markup=builder.as_markup())
            else:
                await bot.send_message(event_chat.id, f"{book_id}.{favorites}{likes} <b>{title}</b> - {authors}, {year}", parse_mode="HTML", reply_markup=builder.as_markup())
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
            favorites = " ⭐" if row.get("favorites") else ""
            likes = " 👍" if row.get("likes") else ""
            emoji = random.choice(["📕", "📘", "📗", "📙"])
            # Prepare the lines to add
            lines_to_add = ""
            if category != prev_category:
                await bot.send_message(event_chat.id, message_text, parse_mode="HTML")
                message_text = ""
                lines_to_add += "📂 <b>"+category+"</b>\n"
                lines_to_add += "——————————————————\n"
                prev_category = category
            lines_to_add += f"{emoji} {book_id}.{favorites}{likes} {title} - {authors}, {year}\n"
            # Check if adding this would exceed the limit
            if len(message_text + lines_to_add) >= engb.MaxCharsInMessage:
                # Send current message and start a new one
                await bot.send_message(event_chat.id, message_text, parse_mode="HTML")
                message_text = lines_to_add
            else:
                message_text += lines_to_add
        # Send any remaining text
        if message_text:
            await bot.send_message(event_chat.id, message_text, parse_mode="HTML")

# -------------------------------------------------------
# Export books to files and send to user
async def ExportBooks(state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    await bot.send_message(event_chat.id, _("exporting_books"))
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT *
            FROM books
            WHERE user_id = $1
            ORDER BY category ASC, book_id ASC
        """, event_from_user.id)
    if len(rows) == 0:
        await bot.send_message(event_chat.id, _("no_books"))
    else:
        # Prepare CSV and JSON data
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
        csv_file = io.StringIO()
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["book_id", "category", "title", "authors", "authors_full_names", "pages", "publisher", "year", "isbn", "favorites", "likes", 
                             "cover_filename", "photo_filename", "brief_filename", "brief2_filename",
                             "brief", "annotation", "datetime"])
        json_list = []

        for row in rows:
            csv_writer.writerow([
                row["book_id"],
                row["category"],
                row["title"],
                row["authors"],
                row["authors_full_names"],
                row["pages"],
                row["publisher"],
                row["year"],
                row["isbn"],
                row["favorites"],
                row["likes"],
                engw.AWS_EXTERNAL_URL + "/" + str(row["cover_filename"]),
                engw.AWS_EXTERNAL_URL + "/" + str(row["photo_filename"]),
                engw.AWS_EXTERNAL_URL + "/" + str(row["brief_filename"]),
                engw.AWS_EXTERNAL_URL + "/" + str(row["brief2_filename"]),
                row["brief"],
                row["annotation"],
                row["datetime"].isoformat()
            ])
            json_list.append({
                "book_id": row["book_id"],
                "category": row["category"],
                "title": row["title"],
                "authors": row["authors"],
                "authors_full_names": row["authors_full_names"],
                "pages": row["pages"],
                "publisher": row["publisher"],
                "year": row["year"],
                "isbn": row["isbn"],
                "favorites": row["favorites"],
                "likes": row["likes"],
                "cover_filename": engw.AWS_EXTERNAL_URL + "/" + str(row["cover_filename"]),
                "photo_filename": engw.AWS_EXTERNAL_URL + "/" + str(row["photo_filename"]),
                "brief_filename": engw.AWS_EXTERNAL_URL + "/" + str(row["brief_filename"]),
                "brief2_filename": engw.AWS_EXTERNAL_URL + "/" + str(row["brief2_filename"]),
                "brief": row["brief"],
                "annotation": row["annotation"],
                "datetime": row["datetime"].isoformat()
            })

        # Send CSV file
        csv_file.seek(0)
        await bot.send_document(
            event_chat.id,
            document=BufferedInputFile(csv_file.getvalue().encode(), filename=f"{timestamp}.csv"),
            caption=_("books_export_csv")
        )

        # Send JSON file
        json_data = json.dumps(json_list, ensure_ascii=False, indent=4)
        await bot.send_document(
            event_chat.id,
            document=BufferedInputFile(json_data.encode(), filename=f"{timestamp}.json"),
            caption=_("books_export_json")
        )

        # Encrypte user ID and send link to web-export
        url = engw.URL_BASE + "lib/" + engw.encrypt_for_url(str(event_from_user.id))
        await bot.send_message(event_chat.id, _("books_{url}_export").format(url=url))

    await h_start.MainMenu(state, pool, bot, event_chat, event_from_user)
    