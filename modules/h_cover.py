# Module for handling bot messages related to prcessing book covers photos

from modules.imports import asyncpg, aioboto3, cv2, async_remove, io, uuid, np, _, env, eng
from modules.imports import Bot, F, Chat, User, Message, ReactionTypeEmoji, BufferedInputFile, InlineKeyboardBuilder, CallbackQuery, FSMContext
import modules.h_brief as h_brief # For run brief commands

# =========================================================
# Order points for perspective transformation
def order_points(pts):
    # Initialize ordered points
    rect = np.zeros((4, 2), dtype=np.float32)
    
    # Top-left point will have the smallest sum
    # Bottom-right point will have the largest sum
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    
    # Top-right point will have the smallest difference
    # Bottom-left point will have the largest difference
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    
    return rect

# =========================================================
# Ask user for the photo of the book cover
async def AskForCover(state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
    # Forget old books: clear all book fields in the state
    await state.update_data(**{key: None for key in (env.BOOK_FIELDS + env.ADVANCED_BOOK_FIELDS + ["book_id"])})
    # Ask for the cover text
    await bot.send_message(event_chat.id, _("photo_cover"))
    # Set the state to wait for the cover text
    await state.set_state(env.State.wait_for_cover_photo)

# =========================================================
# Handler for sended photo of book cover
@eng.base_router.message(env.State.wait_for_cover_photo, F.photo)
async def cover_photo(message: Message, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat, event_from_user: User) -> None:
    # Get the photo from the message
    photo = message.photo[-1]
    photo_file = await bot.get_file(photo.file_id)
    photo_bytesio = await bot.download_file(photo_file.file_path)
    photo_bytes = photo_bytesio.read()
    photo_bytesio2 = io.BytesIO(photo_bytes)

    # Start the S3 client
    session = aioboto3.Session()
    async with session.client(service_name='s3', endpoint_url=eng.AWS_ENDPOINT_URL) as s3:

        # -------------------------------------------------------
        # Upload the photo to S3 storage
        try:
            photo_filename = f"{event_from_user.id}/photo/{uuid.uuid4()}.jpg" # Generate a unique filename for the photo
            await s3.upload_fileobj(photo_bytesio2, eng.AWS_BUCKET_NAME, photo_filename)
            await state.update_data(photo_filename=photo_filename) # Save the filename in the state
            # Give like to user's photo
            await bot.set_message_reaction(chat_id=event_chat.id,
                                           message_id=message.message_id,
                                           reaction=[ReactionTypeEmoji(emoji='👍')])
        except Exception as e:
            await message.reply(_("upload_failed")+f" {e}")
            eng.logging.error(f"Error uploading to S3: {e}")
        
        # -------------------------------------------------------
        # Remove the background from the image
        try:
            photo_bytesio2 = io.BytesIO(photo_bytes)
            output = await async_remove(photo_bytesio2.getvalue())
            output_bytesio = io.BytesIO()
            output_bytesio.write(output) #, format='PNG'
        except Exception as e:
            await message.reply(_("remove_background_failed")+f" {e}")
            eng.logging.error(f"Error removing background: {e}")
        
        # -------------------------------------------------------
        # Found book contour

        try:
            # Load image without background to OpenCV format for contour detection
            nparr = np.frombuffer(output_bytesio.getvalue(), dtype=np.uint8)
            img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Convert for contour detection
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGRA2GRAY)

            # Find contours
            contours, hierarchy = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:

                # Find the largest contour
                largest_contour = max(contours, key=cv2.contourArea)
                
                # Approximate the contour to get a polygon
                epsilon = 0.02 * cv2.arcLength(largest_contour, True)
                approx = cv2.approxPolyDP(largest_contour, epsilon, True)
                
                if len(approx) == 4:
                    # Get dimensions for the output image
                    # Use maximum of width and height to determine orientation
                    width = int((np.linalg.norm(approx[0] - approx[1])+np.linalg.norm(approx[2] - approx[3]))/2)
                    height = int((np.linalg.norm(approx[1] - approx[2])+np.linalg.norm(approx[3] - approx[0]))/2)
                    
                    # Swap width and height if the image is in portrait orientation
                    if width > height:
                        width, height = height, width

                    # Define destination points for perspective transform
                    dst_points = np.array([ [0, 0], [width-1, 0], [width-1, height-1], [0, height-1] ], dtype=np.float32)
                    
                    # Sort source points for correct mapping
                    src_points = np.float32(approx.reshape(4, 2))
                    src_points = order_points(src_points)
                    
                    # Apply perspective transformation
                    matrix = cv2.getPerspectiveTransform(src_points, dst_points)
                    result = cv2.warpPerspective(img_cv, matrix, (width, height))
                    
            is_success, buffer = cv2.imencode('.jpg', result)
            if is_success:
                output_bytesio = io.BytesIO()
                output_bytesio.write(buffer.tobytes())
                output_bytesio.seek(0)
            else:
                await message.reply(_("contour_failed"))
                eng.logging.error("Error detect contour of the book")
        except Exception as e:
            await message.reply(_("contour_failed")+f" {e}")
            eng.logging.error(f"Error processing image: {e}")

        # -------------------------------------------------------
        # Upload the processed image to S3 storage
        try:
            output_bytesio2 = io.BytesIO(output_bytesio.getvalue()) # Save the processed image to a BytesIO object
            cover_filename = f"{event_from_user.id}/cover/{uuid.uuid4()}.jpg" # Generate a unique filename for the photo
            await s3.upload_fileobj(output_bytesio2, eng.AWS_BUCKET_NAME, cover_filename)
            await state.update_data(cover_filename=cover_filename) # Save the filename in the state
        except Exception as e:
            await message.reply(_("upload_failed")+f" {e}")
            eng.logging.error(f"Error uploading to S3: {e}")
        
        # -------------------------------------------------------
        # Send the processed image back to the user
        builder = InlineKeyboardBuilder()
        await eng.RemoveInlineKeyboards(None, state, bot, event_chat)
        for action in env.COVER_ACTIONS:
            builder.button(text=_(action), callback_data=env.CoverActions(action=action) )
        builder.adjust(1)
        sent_message = await bot.send_photo(event_chat.id, photo=BufferedInputFile(output_bytesio.getvalue(), filename=cover_filename), reply_markup=builder.as_markup())
        await state.update_data(inline=sent_message.message_id)
        await state.set_state(env.State.wait_reaction_on_cover)

# =========================================================
# Handler for inline button use_cover
@eng.base_router.callback_query(env.CoverActions.filter(F.action == "use_cover"))
async def use_cover(callback: CallbackQuery, callback_data: env.CoverActions, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
    await eng.RemoveInlineKeyboards(callback, state, bot, event_chat)
    # Give like to cover's photo
    await bot.set_message_reaction(chat_id=event_chat.id,
                                    message_id=callback.message.message_id,
                                    reaction=[ReactionTypeEmoji(emoji='👍')])
    await h_brief.AskForBrief(state, pool, bot, event_chat)

# =========================================================
# Handler for inline button use_original_photo
@eng.base_router.callback_query(env.CoverActions.filter(F.action == "use_original_photo"))
async def use_original_photo(callback: CallbackQuery, callback_data: env.CoverActions, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
    await eng.RemoveInlineKeyboards(callback, state, bot, event_chat)
    data = await state.get_data()
    photo_filename = data.get("photo_filename")
    await state.update_data(cover_filename=photo_filename) # Replace cover by original photo filename
    # Delete the message with the processed cover photo
    try:
        await bot.delete_message(chat_id=event_chat.id, message_id=callback.message.message_id)
    except Exception as e:
        eng.logging.warning(f"Failed to delete callback message: {e}")
    await h_brief.AskForBrief(state, pool, bot, event_chat)

# =========================================================
# Handler for inline button take_new_photo
@eng.base_router.callback_query(env.CoverActions.filter(F.action == "take_new_photo"))
async def take_new_cover_photo(callback: CallbackQuery, callback_data: env.CoverActions, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
    await eng.RemoveInlineKeyboards(callback, state, bot, event_chat)
    await AskForCover(state, pool, bot, event_chat)
