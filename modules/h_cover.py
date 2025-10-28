# Module for handling bot messages related to prcessing book covers photos

from modules.imports import asyncpg, aioboto3, cv2, Image, async_remove, sessionHQ, io, uuid, np, _, env, eng
from modules.imports import Bot, F, Chat, User, Message, ReactionTypeEmoji, BufferedInputFile, InlineKeyboardBuilder, CallbackQuery, FSMContext
import modules.h_brief as h_brief # For run brief commands

# =========================================================
# Calculate distance between two points
def distance(p1, p2):
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

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
        
        # Add temporal message for waiting
        waiting_message = await message.reply(_("wait"))

        # -------------------------------------------------------
        # Remove the background from the image
        try:

            # Remove background
            photo_bytesio2 = io.BytesIO(photo_bytes)
            mask = await async_remove(photo_bytesio2.getvalue(), session=sessionHQ, only_mask=True)
            
            mask = Image.open(io.BytesIO(mask))
            # Different models return different image format
            mask_np = np.array(mask)
            if mask.mode == 'RGBA':
                # Берём только альфа-канал
                mask_bw = mask_np[:, :, 3]
            else:
                mask_bw = mask_np

            # Convert to binary mask
            t, binary_mask = cv2.threshold(mask_bw, 127, 255, cv2.THRESH_BINARY)
            # Apply morphological operations to clean up the mask
            kernel = np.ones((5, 5), np.uint8)
            # Close small holes in the mask
            binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            # Remove small noise outside the mask
            binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel, iterations=2)

            # Find contours
            contours, t = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                raise ValueError(_("contour_failed"))

            # Find the largest contour
            largest_contour = max(contours, key=cv2.contourArea)

            # Approximate the contour to get a quadrilateral
            quadrilateral = None

            for factor in np.arange(0.02, 0.15, 0.005):
                epsilon = factor * cv2.arcLength(largest_contour, True)
                approx = cv2.approxPolyDP(largest_contour, epsilon, True)
                
                if len(approx) == 4:
                    quadrilateral = approx
                    break
                elif len(approx) < 4 and quadrilateral is None:
                    # if just not found 4 points yet, save the best approximation
                    quadrilateral = approx

            # If no quadrilateral found, use minimum area rectangle arround the largest contour
            if quadrilateral is None or len(quadrilateral) != 4:
                # Use minimum area rotated rectangle
                rect = cv2.minAreaRect(largest_contour)
                box = cv2.boxPoints(rect)
                quadrilateral = np.int0(box).reshape(-1, 1, 2)

            # Get quadrilateral points
            pts = quadrilateral.reshape(4, 2).astype(np.float32)

            # Order points: top-left, top-right, bottom-right, bottom-left
            # First sort by sum of coordinates
            rect = np.zeros((4, 2), dtype=np.float32)
            s = pts.sum(axis=1)
            rect[0] = pts[np.argmin(s)]  # top-left (min sum)
            rect[2] = pts[np.argmax(s)]  # bottom-right (max sum)

            # Remain two points sort by difference of coordinates
            diff = np.diff(pts, axis=1)
            rect[1] = pts[np.argmin(diff)]  # top-right (min difference)
            rect[3] = pts[np.argmax(diff)]  # bottom-left (max difference)

            # Compute width and height of the output quadrilateral
            width_top = distance(rect[0], rect[1])
            width_bottom = distance(rect[2], rect[3])
            width = int(max(width_top, width_bottom))

            height_left = distance(rect[0], rect[3])
            height_right = distance(rect[1], rect[2])
            height = int(max(height_left, height_right))

            # Define orientation and create target quadrilateral
            # If height is greater than width, then portrait orientation
            if height > width:
                # Portrait orientation - swap width and height
                dst = np.array([
                    [0, 0],
                    [width - 1, 0],
                    [width - 1, height - 1],
                    [0, height - 1]
                ], dtype=np.float32)
                final_width, final_height = width, height
            else:
                # Landscape orientation
                dst = np.array([
                    [0, 0],
                    [width - 1, 0],
                    [width - 1, height - 1],
                    [0, height - 1]
                ], dtype=np.float32)
                final_width, final_height = width, height

            # Compute perspective transformation matrix
            M = cv2.getPerspectiveTransform(rect, dst)

            # Apply perspective transformation
            original = cv2.imdecode(np.frombuffer(photo_bytes, np.uint8), cv2.IMREAD_COLOR)
            warped = cv2.warpPerspective(original, M, (final_width, final_height))

            is_success, buffer = cv2.imencode('.jpg', warped)
            if is_success:
                output_bytesio = io.BytesIO()
                output_bytesio.write(buffer.tobytes())
                output_bytesio.seek(0)
            else:
                raise ValueError(_("contour_failed"))

        except Exception as e:
            await message.reply(_("remove_background_failed")+f" {e}")
            eng.logging.error(f"Error removing background: {e}")
            return
        
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
        
        # Remove temporal message
        await waiting_message.delete()

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
