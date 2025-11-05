# Module for handling bot messages related to prcessing book annotations

from modules.imports import asyncpg, aioboto3, AsyncOpenAI, io, uuid, base64, _, env, eng
from modules.imports import Bot, F, Chat, User, Message, ReactionTypeEmoji, InlineKeyboardBuilder, CallbackQuery, FSMContext
import modules.book as book # For save book to database
import modules.h_edit as h_edit # For editing book information
import modules.h_cover as h_cover # For do book cover photos
import modules.h_start as h_start # For handling start command

# =========================================================
# Ask user for the photo of the first page of the book with annotation
async def AskForBrief(state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
    # Add keyboard for two photos option
    builder = InlineKeyboardBuilder()
    await eng.RemoveInlineKeyboards(None, state, bot, event_chat)
    builder.button(text=_("take_two_brief_photos"), callback_data=env.BriefPhotos(count=2) )
    builder.adjust(1)
    # Ask for the brief photo
    sent_message = await bot.send_message(event_chat.id, _("photo_brief_1of1"), reply_markup=builder.as_markup())
    await state.update_data(inline=sent_message.message_id)
    # Set the state to wait for the brief photo
    await state.set_state(env.State.wait_for_brief_photo1of1)

# =========================================================
# Handler for inline button take_two_brief_photos
@eng.base_router.callback_query(env.BriefPhotos.filter(F.count == 2))
async def take_two_brief_photos(callback: CallbackQuery, callback_data: env.BriefPhotos, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
    # Remove previous message
    try:
        await callback.message.delete()
    except Exception as e:
        eng.logging.error(f"Error deleting previous message: {e}")
    # Ask for the first brief photo
    sent_message = await bot.send_message(event_chat.id, _("photo_brief_1of2"))
    # Set the state to wait for the first brief photo
    await state.set_state(env.State.wait_for_brief_photo1of2)

# =========================================================
# Handler for sended photo of the first page of the book with annotation
@eng.base_router.message(env.State.wait_for_brief_photo1of1, F.photo)
@eng.base_router.message(env.State.wait_for_brief_photo1of2, F.photo)
@eng.base_router.message(env.State.wait_for_brief_photo2of2, F.photo)
async def brief_photo(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:

    # Get the photo from the message
    photo = message.photo[-1]
    photo_file = await bot.get_file(photo.file_id)
    photo_bytesio = await bot.download_file(photo_file.file_path)
    photo_bytes = photo_bytesio.read()
    photo_bytesio2 = io.BytesIO(photo_bytes)

    # Get state
    current_state = await state.get_state()

    # -------------------------------------------------------
    # Start the S3 client
    session = aioboto3.Session()
    async with session.client(service_name='s3', endpoint_url=eng.AWS_ENDPOINT_URL) as s3:
        # Upload the photo to S3 storage
        try:
            brief_filename = f"{message.from_user.id}/brief/{uuid.uuid4()}.jpg" # Generate a unique filename for the photo
            await s3.upload_fileobj(photo_bytesio2, eng.AWS_BUCKET_NAME, brief_filename)
            if current_state == env.State.wait_for_brief_photo2of2:
                await state.update_data(brief2_filename=brief_filename) # Save the filename in the state
                await state.update_data(brief2_base64 = base64.b64encode(photo_bytesio2.getvalue()).decode('utf-8'))
            else:
                await state.update_data(brief_filename=brief_filename) # Save the filename in the state
                await state.update_data(brief_base64 = base64.b64encode(photo_bytesio2.getvalue()).decode('utf-8'))
            # Give like to user's photo
            await bot.set_message_reaction(chat_id=event_chat.id,
                                           message_id=message.message_id,
                                           reaction=[ReactionTypeEmoji(emoji='👍')])
        except Exception as e:
            await message.reply(_("upload_failed"))
            eng.logging.error(f"Error uploading to S3: {e}")

    # If we are waiting for the second brief photo, ask for it
    if current_state == env.State.wait_for_brief_photo1of2:
        await bot.send_message(event_chat.id, _("photo_brief_2of2"))
        await state.set_state(env.State.wait_for_brief_photo2of2)
        return

    # Add temporal message for waiting
    if current_state == env.State.wait_for_brief_photo2of2:
        waiting_message = await message.reply(_("wait2"))
    else:
        waiting_message = await message.reply(_("wait"))

    # Parse text on the photo using an Vision LLM
    try:
        # Prepare session for OpenAI API        
        client = AsyncOpenAI(
            api_key=eng.GPT_API_TOKEN,
            base_url=eng.GPT_URL
        )
        # Ask GPT-4 Vision to analyze the image and extract book information
        prompt = ""
        for line in env.BOOK_PROMPT:
            prompt = prompt + _(line) + "\n"
        data = await state.get_data()
        VLM_messages = [
                {"role": "user", "content": [ {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{data.get("brief_base64")}"} } ] }
            ]
        if current_state == env.State.wait_for_brief_photo2of2:
            VLM_messages = VLM_messages + [
                    {"role": "user", "content": [ {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{data.get("brief2_base64")}"} } ] }
                ]
        VLM_messages = VLM_messages + [
                {"role": "user", "content": [ {"type": "text", "text": prompt} ] }
            ]
        response = await client.chat.completions.create(
            model=eng.GPT_MODEL,
            messages=VLM_messages,
            max_tokens=2000
        )
    except Exception as e:
        await message.reply(_("gpt_failed"))
        eng.logging.error(f"Error asking GPT: {e}")
    
    try:
        # Convert the response to a dictionary
        response_text = response.choices[0].message.content
        book_dict = {}
        for line in response_text.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                # Prepare dict with book information for computer
                book_dict[key] = value
        await state.update_data(**book_dict) # Save the book information in the state
        if not book_dict:
            raise ValueError()        
    except Exception as e:
        await message.reply(_("gpt_incorrect")+"\n"+response_text)
        eng.logging.error(f"Error parsing GPT response: {e}")

    # Remove temporal message
    await waiting_message.delete()
    # Print book info and ask user for reaction on brief
    await AskForBriefReaction(message, state, pool, bot, event_chat)


# =========================================================
#  Print book info and ask user for reaction on brief
async def AskForBriefReaction(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
    # Print the book information
    sent_message = await book.PrintBook(message, state, pool, bot)
    # Generate keyboard with further actions
    builder = InlineKeyboardBuilder()
    await eng.RemoveInlineKeyboards(None, state, bot, event_chat)
    for action in env.BRIEF_ACTIONS:
        builder.button(text=_(action), callback_data=env.BriefActions(action=action) )
    builder.adjust(2,1)
    # Add to the message with book information the keyboard
    await bot.edit_message_reply_markup(chat_id=event_chat.id, message_id=sent_message.message_id, reply_markup=builder.as_markup())
    await state.update_data(inline=sent_message.message_id)
    await state.set_state(env.State.wait_reaction_on_brief)

# =========================================================
# Handler for inline button use_brief
@eng.base_router.callback_query(env.BriefActions.filter(F.action == "use_brief"))
async def use_brief(callback: CallbackQuery, callback_data: env.BriefActions, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    await eng.RemoveInlineKeyboards(callback, state, bot, event_chat)
    # Give like to brief message
    await bot.set_message_reaction(chat_id=event_chat.id,
                                    message_id=callback.message.message_id,
                                    reaction=[ReactionTypeEmoji(emoji='👍')])
    await book.SaveBookToDatabase(state, pool, bot, event_from_user)
    # Write about added book and ask about the next one
    data = await state.get_data()
    builder = InlineKeyboardBuilder()
    for action in env.NEXT_ACTIONS:
        builder.button(text=_(action), callback_data=env.NextActions(action=action) )
    builder.adjust(2)
    sent_message = await callback.message.answer((_("{bookid}_added")+" "+_("add_next_{category}")).format(bookid=data["book_id"], category=data["category"]), 
                                                 reply_markup=builder.as_markup())
    await state.update_data(inline=sent_message.message_id)
    await state.set_state(env.State.wait_next_book)

# =========================================================
# Handler for inline button edit_brief
@eng.base_router.callback_query(env.BriefActions.filter(F.action == "edit_brief"))
async def edit_brief(callback: CallbackQuery, callback_data: env.BriefActions, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
    await eng.RemoveInlineKeyboards(callback, state, bot, event_chat)
    await h_edit.SelectField(callback.message, state, pool, bot, event_chat)

# =========================================================
# Handler for inline button take_new_photo
@eng.base_router.callback_query(env.BriefActions.filter(F.action == "take_new_photo"))
async def take_new_brief_photo(callback: CallbackQuery, callback_data: env.BriefActions, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
    await eng.RemoveInlineKeyboards(callback, state, bot, event_chat)
    await AskForBrief(state, pool, bot, event_chat)

# =========================================================
# Handler for the callback query when the user selects "add another book"
@eng.base_router.callback_query(env.NextActions.filter(F.action == "add_another_book"))
async def add_another_book(callback: CallbackQuery, callback_data: env.NextActions, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
    await eng.RemoveInlineKeyboards(callback, state, bot, event_chat)
    await h_cover.AskForCover(state, pool, bot, event_chat)

# =========================================================
# Handler for the callback query when the user selects "do not add another book"
@eng.base_router.callback_query(env.NextActions.filter(F.action == "no_another_book"))
async def no_another_book(callback: CallbackQuery, callback_data: env.NextActions, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    await eng.RemoveInlineKeyboards(callback, state, bot, event_chat)
    await h_start.MainMenu(state, pool, bot, event_chat, event_from_user)
