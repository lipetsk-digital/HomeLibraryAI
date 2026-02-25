# Module for handling bot messages related to prcessing book annotations

import modules.engine as eng # For crossplatform bot engine functions and definitions
from modules.engine import _  # For internationalization and localization
import modules.actions as act # For bot commands and actions
import modules.environment as env # For bot states and callback data factories
import modules.common as com # For common functions and definitions
import modules.book as book # For save book to database

#import modules.h_edit as h_edit # For editing book information
import modules.h_cover as h_cover # For do book cover photos
import modules.h_start as h_start # For handling start command

import logging # For logging
import uuid # For generating unique filenames
import aioboto3 # For AWS S3 storage
import io # For handling byte streams
import base64 # For encoding and decoding base64
from openai import AsyncOpenAI # For OpenAI API client

# =========================================================
# Ask user for the photo of the first page of the book with annotation
async def AskForBrief(state: eng.FSMContext, event_chat: eng.Chat) -> None:
    # Add keyboard for two photos option
    keyboard = []
    keyboard.append(eng.CallbackButton(text=_("take_two_brief_photos"), payload=env.BriefPhotos(count=2)))
    # Ask for the brief photo
    sent_message = await eng.send_message(event_chat.id, _("photo_brief_1of1"))
    await eng.send_inline_keyboard(sent_message, keyboard, state, 1, eng.onButtonClick.RemoveKeyboardKeepMessage)
    # Set the state to wait for the brief photo
    await state.set_state(env.State.wait_for_brief_photo1of1)

# =========================================================
# Handler for inline button take_two_brief_photos
@eng.on_callback(eng.base_router,env.BriefPhotos.filter(eng.F.count == 2))
@eng.callback_handler
async def take_two_brief_photos(message: eng.Message, callback: eng.CallbackData, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:
    # Remove previous message
    try:
        await callback.message.delete()
    except Exception as e:
        logging.error(f"Error deleting previous message: {e}")
    # Ask for the first brief photo
    sent_message = await eng.send_message(event_chat.id, _("photo_brief_1of2"))
    # Set the state to wait for the first brief photo
    await state.set_state(env.State.wait_for_brief_photo1of2)

# =========================================================
# Handler for sended photo of the first page of the book with annotation
@eng.on_message(eng.base_router,env.State.wait_for_brief_photo1of1, eng.F_photo())
@eng.on_message(eng.base_router,env.State.wait_for_brief_photo1of2, eng.F_photo())
@eng.on_message(eng.base_router,env.State.wait_for_brief_photo2of2, eng.F_photo())
@eng.message_handler
async def brief_photo(message: eng.Message, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:

    # Get the photo from the message
    photo = await message.get_photo()
    photo_bytesio = io.BytesIO(photo.body)

    # Get state
    current_state = await state.get_state()

    # -------------------------------------------------------
    # Start the S3 client
    session = aioboto3.Session()
    async with session.client(service_name='s3', endpoint_url=com.AWS_ENDPOINT_URL) as s3:
        # Upload the photo to S3 storage
        try:
            brief_filename = f"{message.from_user.id}/brief/{uuid.uuid4()}.jpg" # Generate a unique filename for the photo
            await s3.upload_fileobj(photo_bytesio, com.AWS_BUCKET_NAME, brief_filename)
            if current_state == env.State.wait_for_brief_photo2of2:
                await state.update_data(brief2_filename=brief_filename) # Save the filename in the state
                await state.update_data(brief2_base64 = base64.b64encode(photo_bytesio.getvalue()).decode('utf-8'))
            else:
                await state.update_data(brief_filename=brief_filename) # Save the filename in the state
                await state.update_data(brief_base64 = base64.b64encode(photo_bytesio.getvalue()).decode('utf-8'))
            await message.set_like() # Give like to user's photo
        except Exception as e:
            await message.reply(_("upload_failed"))
            logging.error(f"Error uploading to S3: {e}")

    # If we are waiting for the second brief photo, ask for it
    if current_state == env.State.wait_for_brief_photo1of2:
        await eng.send_message(event_chat.id, _("photo_brief_2of2"))
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
            api_key=com.GPT_API_TOKEN,
            base_url=com.GPT_URL
        )
        # Ask GPT-4 Vision to analyze the image and extract book information
        prompt = ""
        for line in act.BOOK_PROMPT:
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
            model=com.GPT_MODEL,
            messages=VLM_messages,
            max_tokens=2000
        )
    except Exception as e:
        await message.reply(_("gpt_failed"))
        logging.error(f"Error asking GPT: {e}")
    
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
        logging.error(f"Error parsing GPT response: {e}")

    # Remove temporal message
    await waiting_message.delete()
    # Print book info and ask user for reaction on brief
    await AskForBriefReaction(message, state, event_chat)


# =========================================================
#  Print book info and ask user for reaction on brief
async def AskForBriefReaction(message: eng.Message, state: eng.FSMContext, event_chat: eng.Chat) -> None:
    # Print the book information
    sent_message = await book.PrintBook(message, state)
    # Generate keyboard with further actions
    keyboard = []
    for action in act.BRIEF_ACTIONS:
        keyboard.append(eng.CallbackButton(text=_(action), payload=env.BriefActions(action=action)))
    # Add to the message with book information the keyboard
    await eng.send_inline_keyboard(sent_message, keyboard, state, 2, eng.onButtonClick.RemoveKeyboardKeepMessage)
    await state.set_state(env.State.wait_reaction_on_brief)

# =========================================================
# Handler for inline button use_brief
@eng.on_callback(eng.base_router,env.BriefActions.filter(eng.F.action == "use_brief"))
@eng.callback_handler
async def use_brief(message: eng.Message, callback: eng.CallbackData, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:
    await message.set_like() # Give like to brief
    await book.SaveBookToDatabase(state, event_from_user)
    # Write about added book and ask about the next one
    data = await state.get_data()
    keyboard = []
    for action in act.NEXT_ACTIONS:
        keyboard.append(eng.CallbackButton(text=_(action), payload=env.NextActions(action=action)))
    sent_message = await message.reply((_("{bookid}_added")+" "+_("add_next_{category}")).format(bookid=data["book_id"], category=data["category"]))
    await eng.send_inline_keyboard(sent_message, keyboard, state, 2)
    await state.set_state(env.State.wait_next_book)
'''

# =========================================================
# Handler for inline button edit_brief
@engt.base_router.callback_query(env.BriefActions.filter(F.action == "edit_brief"))
async def edit_brief(callback: CallbackQuery, callback_data: env.BriefActions, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
    await engt.RemoveInlineKeyboards(callback, state, bot, event_chat)
    await h_edit.SelectField(callback.message, state, pool, bot, event_chat)

# =========================================================
# Handler for inline button favorites and likes
@engt.base_router.callback_query(env.BriefActions.filter(F.action == "favorites"))
@engt.base_router.callback_query(env.BriefActions.filter(F.action == "likes"))
async def favorites(callback: CallbackQuery, callback_data: env.BriefActions, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
    await engt.RemoveInlineKeyboards(callback, state, bot, event_chat)
    # Inverse boolean field value
    action = callback_data.action
    data = await state.get_data()
    old_value = data[action]
    new_value = not old_value
    book_dict = {}
    book_dict[action] = new_value
    await state.update_data(**book_dict)
    # Update the book information
    await AskForBriefReaction(callback.message, state, pool, bot, event_chat)

# =========================================================
# Handler for inline button take_new_photo
@engt.base_router.callback_query(env.BriefActions.filter(F.action == "take_new_photo"))
async def take_new_brief_photo(callback: CallbackQuery, callback_data: env.BriefActions, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
    await engt.RemoveInlineKeyboards(callback, state, bot, event_chat)
    await AskForBrief(state, pool, bot, event_chat)

# =========================================================
# Handler for the callback query when the user selects "add another book"
@engt.base_router.callback_query(env.NextActions.filter(F.action == "add_another_book"))
async def add_another_book(callback: CallbackQuery, callback_data: env.NextActions, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
    await engt.RemoveInlineKeyboards(callback, state, bot, event_chat)
    await h_cover.AskForCover(state, pool, bot, event_chat)

# =========================================================
# Handler for the callback query when the user selects "do not add another book"
@engt.base_router.callback_query(env.NextActions.filter(F.action == "no_another_book"))
async def no_another_book(callback: CallbackQuery, callback_data: env.NextActions, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    await engt.RemoveInlineKeyboards(callback, state, bot, event_chat)
    await h_start.MainMenu(state, pool, bot, event_chat, event_from_user)
'''