# ========================================================
# Module for handling bot messages related to prcessing book covers photos
# ========================================================
import asyncpg # For asynchronous PostgreSQL connection
import boto3 # For AWS S3 storage
from aiogram import Bot, F # For Telegram bot framework
from aiogram import Router # For creating a router for handling messages
from aiogram.types import Message # For Telegram message handling
from aiogram.fsm.context import FSMContext # For finite state machine context
from aiogram.utils.i18n import gettext as _ # For internationalization and localization
from aiogram.filters.command import Command # For command handling
from aiogram.types.callback_query import CallbackQuery # For handling callback queries
from aiogram.utils.keyboard import InlineKeyboardBuilder # For creating inline keyboards

import modules.environment as env # For environment variables and configurations
import modules.h_start as h_start # For handling start command

# Router for handling messages related to processing book covers photos
cover_router = Router()

# Handler for sended photo of book cover
@cover_router.message(env.State.wait_for_cover_photo, F.photo)
async def cover_photo(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot) -> None:
    # Get the photo from the message
    photo = message.photo[-1]
    photo_file = await bot.get_file(photo.file_id)
    photo_bytesio = await bot.download_file(photo_file.file_path)
    # Save the photo to a local file
    local_file_path = "photo.jpg"
    with open(local_file_path, "wb") as local_file:
        local_file.write(photo_bytesio.read())
    photo_bytesio.seek(0)  # Reset the BytesIO stream position

    # Configure the S3 client
    s3 = boto3.client(endpoint_url=env.AWS_ENDPOINT_URL, service_name='s3')

    # Upload the photo to S3 storage
    try:
        s3.upload_fileobj(photo_bytesio, env.AWS_BUCKET_NAME, 'file.jpg')
        await message.reply(_("Photo uploaded successfully to S3 storage"))
    except Exception as e:
        await message.reply(_("Failed to upload photo to S3 storage"))
        print(f"Error uploading to S3: {e}")


