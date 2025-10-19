# ========================================================
# Module for handling bot messages related to prcessing book annotations
# ========================================================
import asyncpg # For asynchronous PostgreSQL connection
import aioboto3 # For AWS S3 storage
import io # For handling byte streams
import uuid # For generating unique filenames
import base64 # For encoding and decoding base64
from aiogram import Bot, F # For Telegram bot framework
from aiogram import Router # For creating a router for handling messages
from aiogram.types import Message, ReactionTypeEmoji, BufferedInputFile # For Telegram message handling
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.context import FSMContext # For finite state machine context
from aiogram.utils.i18n import gettext as _ # For internationalization and localization
from aiogram.filters.command import Command # For command handling
from aiogram.types.callback_query import CallbackQuery # For handling callback queries
from aiogram.utils.keyboard import InlineKeyboardBuilder # For creating inline keyboards
from openai import AsyncOpenAI # For OpenAI API client

import modules.environment as env # For environment variables and configurations
import modules.book as book # For save book to database
import modules.h_field as h_field # For editing book information

# Router for handling messages related to processing book annotations
brief_router = Router()

# =========================================================
# Ask user for the photo of the first page of the book with annotation
async def AskForBrief(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    # Ask for the brief text
    await message.answer(_("photo_brief"))
    # Set the state to wait for the brief text
    await state.set_state(env.State.wait_for_brief_photo)

# =========================================================
# Handler for sended photo of the first page of the book with annotation
@brief_router.message(env.State.wait_for_brief_photo, F.photo)
async def brief_photo(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    # Get the photo from the message
    photo = message.photo[-1]
    photo_file = await bot.get_file(photo.file_id)
    photo_bytesio = await bot.download_file(photo_file.file_path)
    photo_bytes = photo_bytesio.read()
    photo_bytesio2 = io.BytesIO(photo_bytes)

    # Start the S3 client
    session = aioboto3.Session()
    async with session.client(service_name='s3', endpoint_url=env.AWS_ENDPOINT_URL) as s3:

        # Upload the photo to S3 storage
        try:
            brief_filename = f"{message.from_user.id}/brief/{uuid.uuid4()}.jpg" # Generate a unique filename for the photo
            await s3.upload_fileobj(photo_bytesio2, env.AWS_BUCKET_NAME, brief_filename)
            await state.update_data(brief_filename=brief_filename) # Save the filename in the state
            # Give like to user's photo
            await bot.set_message_reaction(chat_id=message.chat.id,
                                           message_id=message.message_id,
                                           reaction=[ReactionTypeEmoji(emoji='👍')])
        except Exception as e:
            await message.reply(_("upload_failed"))
            env.logging.error(f"Error uploading to S3: {e}")

    try:
        # Prepare session for OpenAI API        
        img_base64 = base64.b64encode(photo_bytesio2.getvalue()).decode('utf-8')
        client = AsyncOpenAI(
            api_key=env.GPT_API_TOKEN,
            base_url=env.GPT_URL
        )
        # Ask GPT-4 Vision to analyze the image and extract book information
        prompt = ""
        for line in env.BOOK_PROMPT:
            prompt = prompt + _(line) + "\n"
        response = await client.chat.completions.create(
            model=env.GPT_MODEL,
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{img_base64}"
                    }}
                ]}
            ],
            max_tokens=2000
        )
    except Exception as e:
        await message.reply(_("gpt_failed"))
        env.logging.error(f"Error asking GPT: {e}")
    
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
        env.logging.error(f"Error parsing GPT response: {e}")

    # Print the book information
    sent_message = await book.PrintBook(message, state, pool, bot)
    # Generate keyboard with further actions
    builder = InlineKeyboardBuilder()
    await env.RemoveOldInlineKeyboards(state, message.chat.id, bot)
    for action in env.BRIEF_ACTIONS:
        builder.button(text=_(action), callback_data=env.BriefActions(action=action) )
    builder.adjust(2,1)
    # Add to the message with book information the keyboard
    await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=sent_message.message_id, reply_markup=builder.as_markup())
    await state.update_data(inline=sent_message.message_id)
    await state.set_state(env.State.wait_reaction_on_brief)

# Handler for inline button use_brief
@brief_router.callback_query(env.BriefActions.filter(F.action == "use_brief"))
async def use_brief(callback: CallbackQuery, callback_data: env.Category, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    await env.RemoveMyInlineKeyboards(callback, state)
    # Give like to brief message
    await bot.set_message_reaction(chat_id=callback.message.chat.id,
                                    message_id=callback.message.message_id,
                                    reaction=[ReactionTypeEmoji(emoji='👍')])
    await book.SaveBookToDatabase(callback, state, pool, bot)
    # Write about added book and ask about the next one
    data = await state.get_data()
    builder = InlineKeyboardBuilder()
    await env.RemoveOldInlineKeyboards(state, callback.message.chat.id, bot)
    for action in env.NEXT_ACTIONS:
        builder.button(text=_(action), callback_data=env.NextActions(action=action) )
    builder.adjust(2)
    sent_message = await callback.message.answer((_("{bookid}_added")+" "+_("add_next_{category}")).format(bookid=data["book_id"], category=data["category"]), 
                                                 reply_markup=builder.as_markup())
    await state.update_data(inline=sent_message.message_id)
    await state.set_state(env.State.wait_next_book)

# Handler for inline button edit_brief
@brief_router.callback_query(env.BriefActions.filter(F.action == "edit_brief"))
async def edit_brief(callback: CallbackQuery, callback_data: env.Category, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    await env.RemoveMyInlineKeyboards(callback, state)
    await h_field.SelectField(callback.message, state, pool, bot)

# Handler for inline button take_new_photo
@brief_router.callback_query(env.BriefActions.filter(F.action == "take_new_photo"))
async def take_new_brief_photo(callback: CallbackQuery, callback_data: env.Category, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    await env.RemoveMyInlineKeyboards(callback, state)
    await AskForBrief(callback.message, state, pool, bot)
