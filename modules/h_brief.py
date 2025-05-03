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
from aiogram.utils.formatting import Text, as_list, as_key_value # For formatting messages
from aiogram.utils.i18n import gettext as _ # For internationalization and localization
from aiogram.filters.command import Command # For command handling
from aiogram.types.callback_query import CallbackQuery # For handling callback queries
from aiogram.utils.keyboard import InlineKeyboardBuilder # For creating inline keyboards
from openai import AsyncOpenAI # For OpenAI API client

import modules.environment as env # For environment variables and configurations

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
# Handler for sended photo of book cover
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
            photo_filename = f"{message.from_user.id}/brief/{uuid.uuid4()}.jpg" # Generate a unique filename for the photo
            await s3.upload_fileobj(photo_bytesio2, env.AWS_BUCKET_NAME, photo_filename)
            await state.update_data(photo_filename=photo_filename) # Save the filename in the state
            # Give like to user's photo
            await bot.set_message_reaction(chat_id=message.chat.id,
                                           message_id=message.message_id,
                                           reaction=[ReactionTypeEmoji(emoji='👍')])
        except Exception as e:
            await message.reply(_("upload_failed"))
            env.logging.error(f"Error uploading to S3: {e}")

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
        model="vis-google/gemini-pro-vision",
        messages=[
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{img_base64}"
                }}
            ]}
        ],
        max_tokens=1000
    )
    
    # Convert the response to a dictionary
    response_text = response.choices[0].message.content
    book = {}
    for line in response_text.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            book[_(key.strip())] = value.strip()
    
    # Generate a message with the book information
    items = []
    for key, value in book.items():
        items.append(as_key_value(key, value))
    content = as_list(*items)
    await message.answer(**content.as_kwargs())

