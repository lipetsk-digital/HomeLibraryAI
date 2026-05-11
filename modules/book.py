# Module for get and put books to database

import modules.engine as eng # For crossplatform bot engine functions and definitions
from modules.engine import _  # For internationalization and localization
import modules.database as db # For database functions and definitions
import modules.environment as env # For bot states and callback data factories
import modules.actions as act # For bot commands and actions
import modules.web as web # For web-related functions and definitions

import modules.h_start as h_start # For handling start command

import random # For random choices
import aiohttp # For async HTTP requests
from datetime import datetime # For handling date and time
import csv # For CSV handling
import json # For JSON handling
import io # For in-memory file handling

# -------------------------------------------------------
# Send a brief statistic about the user's library
async def BriefStatistic(event_from_user: eng.User, event_chat: eng.Chat) -> eng.Message:
    async with db.pool.acquire() as conn:
        result = await conn.fetchval("""SELECT count(*) FROM books WHERE "platform"=$1 AND "user_id"=$2""", eng.MESSENGER, event_from_user.id)
    if (result is None) or (result == 0):
        message = await eng.send_message(chat_id=event_chat.id, text=_("no_books"))
    else:
        message = await eng.send_message(chat_id=event_chat.id, text=_("{result}_book","{result}_books",result).format(result=result))
    return message

# -------------------------------------------------------
# Send to user current book information from user's data and return Message object
async def PrintBook(message: eng.Message, state: eng.FSMContext) -> eng.Message:
    # Get the book data from the state
    data = await state.get_data() # Get stored user's data
    text = ""
    # Loop through the book fields and add them to the items list
    for field in ["book_id"] + act.PUBLIC_BOOK_FIELDS + ["category"]:
        if field in data:
            value = data[field]
            if value:
                if (field == "favorites") or (field == "likes"):
                    text += _(field) + "\n"
                else:
                    text += "<b>" + _(field) + ":</b> " + str(value) + "\n"
    text = text.strip() # Remove trailing newline
    # Send the message with the book information and the keyboard
    sent_message = await message.reply(text=text, parse_mode=eng.ParseMode.HTML)
    return sent_message

# -------------------------------------------------------
# Save book to database
async def SaveBookToDatabase(state: eng.FSMContext, event_from_user: eng.User) -> None:
    # Get stored user's data
    data = await state.get_data()
    data["user_id"] = event_from_user.id
    data["platform"] = eng.MESSENGER
    # Build book dictionary
    fields = act.PUBLIC_BOOK_FIELDS + act.HIDDEN_BOOK_FIELDS
    for field in fields:
        if field not in data:
            data[field] = None
    if data["book_id"]: # If book_id is already set, we are updating existing book
        book_id = data["book_id"]
        # Update the book data in the database
        async with db.pool.acquire() as connection:
            await connection.execute(
                f"UPDATE books SET {', '.join([f'{field} = ${i + 2}' for i, field in enumerate(fields)])} WHERE user_id = $1 AND book_id = ${len(fields) + 2} AND platform = ${len(fields) + 3}",
                event_from_user.id,
                *[data[field] for field in fields],
                book_id,
                eng.MESSENGER
            )
    else:
        # Select max book_id of current user from the database
        async with db.pool.acquire() as connection:
            result = await connection.fetchval("SELECT COALESCE(MAX(book_id),0) FROM books WHERE user_id = $1", event_from_user.id)
            book_id = result + 1 # Increment the max book_id by 1
        # Add manual fields
        data["book_id"] = book_id # Add book ID to the book data
        data["platform"] = eng.MESSENGER # Add platform to the book data
        await state.update_data(book_id=book_id) # Save book ID in the state
        # Insert the book data into the database
        async with db.pool.acquire() as connection:
            await connection.execute(
                f"INSERT INTO books ({', '.join(fields)}) VALUES ({', '.join(['$' + str(i + 1) for i in range(len(fields))])})",
                *[data[field] for field in fields]
            )

# -------------------------------------------------------
# Loop through books dataset and send to user the books list
async def PrintBooksList(rows: list, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:
    # For short list of the books:
    if len(rows) == 0:
        await eng.send_message(event_chat.id, _("no_books_found"))
    elif len(rows) < 10:
        await eng.send_message(event_chat.id, _("{books}_found","{books}_founds",len(rows)).format(books=len(rows)))
        # Send one message for each book with title, authors, year and cover photo
        prev_category = None
        for row in rows:
            book_id = row.get("book_id")
            title = row.get("title")
            authors = row.get("authors")
            year = row.get("year")
            photo = row.get("cover_filename")
            token = row.get("cover_token")
            category = row.get("category")
            favorites = " ⭐" if row.get("favorites") else ""
            likes = " 👍" if row.get("likes") else ""
            if category != prev_category:
                await eng.send_message(event_chat.id, "📂 <b>"+category+"</b>", parse_mode=eng.ParseMode.HTML)
                prev_category = category
            keyboard = []
            keyboard.append(eng.CallbackButton(text=_("edit"), payload=env.EditBook(book_id=book_id)))
            caption = f"{book_id}.{favorites}{likes} <b>{title}</b> - {authors}, {year}"
            if token:
                photo_url = web.AWS_EXTERNAL_URL + "/" + photo
                message = await eng.send_photo_from_token(event_chat.id, token=token, url=photo_url, caption=caption, parse_mode=eng.ParseMode.HTML)
            elif photo:
                photo_url = web.AWS_EXTERNAL_URL + "/" + photo
                # Download books cover from S3 storage
                async with aiohttp.ClientSession() as session:
                    async with session.get(photo_url, timeout=aiohttp.ClientTimeout(total=eng.HTTP_TIMEOUT_sec)) as resp:
                        resp.raise_for_status()
                        photo_bytes = await resp.read()
                message = await eng.send_photo_from_bytes(event_chat.id, photo_bytes=photo_bytes, filename=photo, caption=caption, parse_mode=eng.ParseMode.HTML)
                photo = await message.get_photo()
                # Update loaded to messenger cover token in the database
                async with db.pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE books
                        SET cover_token = $1
                        WHERE book_id = $2 AND user_id = $3 AND platform = $4
                    """, photo.token, book_id, event_from_user.id, eng.MESSENGER)
            else:
                message = await eng.send_message(event_chat.id, caption, parse_mode=eng.ParseMode.HTML)
            await eng.send_inline_keyboard(message, keyboard, state, 1, eng.onButtonClick.KeepKeyboardAndMessage)
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
                await eng.send_message(event_chat.id, message_text, parse_mode=eng.ParseMode.HTML)
                message_text = ""
                lines_to_add += "📂 <b>"+category+"</b>\n"
                lines_to_add += "——————————————————\n"
                prev_category = category
            lines_to_add += f"{emoji} {book_id}.{favorites}{likes} {title} - {authors}, {year}\n"
            # Check if adding this would exceed the limit
            if len(message_text + lines_to_add) >= eng.MaxCharsInMessage:
                # Send current message and start a new one
                await eng.send_message(event_chat.id, message_text, parse_mode=eng.ParseMode.HTML)
                message_text = lines_to_add
            else:
                message_text += lines_to_add
        # Send any remaining text
        if message_text:
            await eng.send_message(event_chat.id, message_text, parse_mode=eng.ParseMode.HTML)

# -------------------------------------------------------
# Export books to files and send to user
async def ExportBooks(state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:
    await eng.send_message(event_chat.id, _("exporting_books"))
    async with db.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT *
            FROM books
            WHERE user_id = $1
            ORDER BY category ASC, book_id ASC
        """, event_from_user.id)
    if len(rows) == 0:
        await eng.send_message(event_chat.id, _("no_books"))
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
                web.AWS_EXTERNAL_URL + "/" + str(row["cover_filename"]),
                web.AWS_EXTERNAL_URL + "/" + str(row["photo_filename"]),
                web.AWS_EXTERNAL_URL + "/" + str(row["brief_filename"]),
                web.AWS_EXTERNAL_URL + "/" + str(row["brief2_filename"]),
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
                "cover_filename": web.AWS_EXTERNAL_URL + "/" + str(row["cover_filename"]),
                "photo_filename": web.AWS_EXTERNAL_URL + "/" + str(row["photo_filename"]),
                "brief_filename": web.AWS_EXTERNAL_URL + "/" + str(row["brief_filename"]),
                "brief2_filename": web.AWS_EXTERNAL_URL + "/" + str(row["brief2_filename"]),
                "brief": row["brief"],
                "annotation": row["annotation"],
                "datetime": row["datetime"].isoformat()
            })

        # Send CSV file
        csv_file.seek(0)
        await eng.send_file_from_bytes(
            event_chat.id,
            file_bytes=csv_file.getvalue().encode(),
            filename=f"{timestamp}.csv",
            caption=_("books_export_csv")
        )

        # Send JSON file
        json_data = json.dumps(json_list, ensure_ascii=False, indent=4)
        await eng.send_file_from_bytes(
            event_chat.id,
            file_bytes=json_data.encode(),
            filename=f"{timestamp}.json",
            caption=_("books_export_json")
        )

        # Encrypte user ID and send link to web-export
        url = web.URL_BASE + "lib/" + web.encrypt_for_url(str(event_from_user.id))
        await eng.send_message(event_chat.id, _("books_{url}_export").format(url=url))

    await h_start.MainMenu(state, event_chat, event_from_user)