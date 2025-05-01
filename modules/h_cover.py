# ========================================================
# Module for handling bot messages related to prcessing book covers photos
# ========================================================
import asyncpg # For asynchronous PostgreSQL connection
import aioboto3 # For AWS S3 storage
import io # For handling byte streams
from rembg import remove # For removing background from images
from PIL import Image # For image processing
from aiogram import Bot, F # For Telegram bot framework
from aiogram import Router # For creating a router for handling messages
from aiogram.types import Message, ReactionTypeEmoji, BufferedInputFile, InputMediaPhoto, InputFile # For Telegram message handling
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
    photo_bytes = photo_bytesio.read()
    photo_bytesio2 = io.BytesIO(photo_bytes)

    # Start the S3 client
    session = aioboto3.Session()
    async with session.client(service_name='s3', endpoint_url=env.AWS_ENDPOINT_URL) as s3:

        # Upload the photo to S3 storage
        try:
            await s3.upload_fileobj(photo_bytesio2, env.AWS_BUCKET_NAME, 'file.jpg')
            # Give like to user's photo
            await bot.set_message_reaction(chat_id=message.chat.id,
                                           message_id=message.message_id,
                                           reaction=[ReactionTypeEmoji(emoji='👍')])
            #sent_message = await message.answer(_("loaded_wait"))
        except Exception as e:
            await message.reply(_("upload_failed"))
            env.logging.error(f"Error uploading to S3: {e}")

        # Remove the background from the image
        try:
            photo_bytesio2 = io.BytesIO(photo_bytes)
            img = Image.open(photo_bytesio2)
            output = remove(img)
            output_bytesio = io.BytesIO()
            output.save(output_bytesio, format='PNG') #, format='PNG'
            output_bytesio2 = io.BytesIO(output_bytesio.getvalue()) # Save the processed image to a BytesIO object
        except Exception as e:
            await message.reply(_("remove_background_failed"))
            env.logging.error(f"Error removing background: {e}")

        # Upload the processed image to S3 storage
        try:
            await s3.upload_fileobj(output_bytesio2, env.AWS_BUCKET_NAME, 'file_processed.jpg')
        except Exception as e:
            await message.reply(_("upload_failed"))
            env.logging.error(f"Error uploading to S3: {e}")

        # Send the processed image back to the user
        bio = io.BytesIO()
        bio.name = 'image.png'
        output.save(bio, 'PNG')
        bio.seek(0)
        output_bytesio2 = io.BytesIO(output_bytesio.getvalue())
        await bot.send_photo(message.chat.id, photo=BufferedInputFile(output_bytesio.getvalue(), filename='result.png'))
        
        #output_bytesio2.seek(0)
        #await bot.send_photo(chat_id=message.chat.id,
        #                        photo=output_bytesio2,
        #                        caption=_("cover_processed"))


