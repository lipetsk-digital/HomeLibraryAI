# Module for handling bot messages related to prcessing book covers photos

import modules.engine as eng # For crossplatform bot engine functions and definitions
from modules.engine import _  # For internationalization and localization
import modules.actions as act # For bot commands and actions
import modules.environment as env # For bot states and callback data factories
import modules.database as db # For database functions and definitions
import modules.book as book # For book routines
import modules.common as com # For common functions and definitions
import aiohttp # For HTTP requests to rembg service
#import modules.h_brief as h_brief # For run brief commands

import logging # For logging
import numpy as np # For arrays processing
import aioboto3 # For AWS S3 storage
import io # For handling byte streams
import uuid # For generating unique filenames
import cv2 # For image processing

# =========================================================
# Calculate distance between two points
def distance(p1, p2):
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

# =========================================================
# Ask user for the photo of the book cover
async def AskForCover(state: eng.FSMContext, event_chat: eng.Chat) -> None:
    # Forget old books: clear all book fields in the state
    values = {}
    for key in (act.PUBLIC_BOOK_FIELDS + act.HIDDEN_BOOK_FIELDS):
        if key != "category":
            values[key] = None
    await state.update_data(**values)
    # Ask for the cover text
    await eng.send_message(event_chat.id, _("photo_cover"))
    # Set the state to wait for the cover text
    await state.set_state(env.State.wait_for_cover_photo)

# =========================================================
# Handler for sended photo of book cover
@eng.on_message(eng.base_router, env.State.wait_for_cover_photo, eng.F_photo())
@eng.message_handler
async def cover_photo(message: eng.Message, state: eng.FSMContext, event_chat: eng.Chat, event_from_user: eng.User) -> None:
    # Initialize variables for cleanup
    photo_bytesio = None
    photo_bytesio2 = None
    output_bytesio = None
    output_bytesio2 = None
    waiting_message = None
    
    # Variables for numpy arrays to cleanup
    mask_np = None
    mask_bw = None
    binary_mask = None
    kernel = None
    original = None
    warped = None
    buffer = None
    
    try:
        photo = await eng.get_photo(message)
        photo_bytesio = io.BytesIO(photo.body)

        # Start the S3 client
        session = aioboto3.Session()
        async with session.client(service_name='s3', endpoint_url=com.AWS_ENDPOINT_URL) as s3:

            # -------------------------------------------------------
            # Upload the photo to S3 storage
            try:
                photo_filename = f"{event_from_user.id}/photo/{uuid.uuid4()}.jpg" # Generate a unique filename for the photo
                await s3.upload_fileobj(photo_bytesio, com.AWS_BUCKET_NAME, photo_filename)
                await state.update_data(photo_filename=photo_filename) # Save the filename in the state
                await eng.set_like(message) # Give like to user's photo
            except Exception as e:
                await message.reply(_("upload_failed")+f" {e}")
                logging.error(f"Error uploading to S3: {e}")
            finally:
                # Close BytesIO after upload
                if photo_bytesio:
                    photo_bytesio.close()
                    photo_bytesio = None
            
            # Add temporal message for waiting
            # Check queue size before processing
            async with aiohttp.ClientSession() as http_session:
                async with http_session.get(f"{com.REMBG_URL}/queue") as resp:
                    queue_data = await resp.json()
                    queue_size = queue_data.get("queue_size", 0)
            if queue_size > 0:
                waiting_message = await message.reply(_("{wait}_in_queue","{wait}_in_queues",queue_size).format(wait=queue_size))
            else:
                waiting_message = await message.reply(_("wait"))

            # -------------------------------------------------------
            # Remove the background from the image
            try:
                # Remove background via rembg service
                photo_bytesio = io.BytesIO(photo.body)
                async with aiohttp.ClientSession() as http_session:
                    async with http_session.post(
                        f"{com.REMBG_URL}/remove?only_mask=true",
                        data=photo_bytesio.getvalue(),
                    ) as resp:
                        if resp.status != 200:
                            raise Exception(f"rembg service error: {resp.status} {await resp.text()}")
                        mask_bytes = await resp.read()
                
                # Decode mask using cv2
                mask_np = cv2.imdecode(np.frombuffer(mask_bytes, np.uint8), cv2.IMREAD_UNCHANGED)
                del mask_bytes  # Free mask bytes immediately
                
                # Different models return different image format
                if mask_np.ndim == 3 and mask_np.shape[2] == 4:
                    # RGBA format - take only alpha channel
                    mask_bw = mask_np[:, :, 3].copy()
                elif mask_np.ndim == 3:
                    # RGB format - convert to grayscale
                    mask_bw = cv2.cvtColor(mask_np, cv2.COLOR_BGR2GRAY)
                else:
                    # Already grayscale
                    mask_bw = mask_np.copy()
                
                # Free mask_np as we don't need it anymore
                del mask_np
                mask_np = None

                # Convert to binary mask
                _none, binary_mask = cv2.threshold(mask_bw, 127, 255, cv2.THRESH_BINARY)
                
                # Free mask_bw as we don't need it anymore
                del mask_bw
                mask_bw = None
                
                # Apply morphological operations to clean up the mask
                kernel = np.ones((5, 5), np.uint8)
                # Close small holes in the mask
                binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
                # Remove small noise outside the mask
                binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel, iterations=2)
                
                # Free kernel
                del kernel
                kernel = None

                # Find contours
                contours, _none = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # Free binary_mask as we don't need it anymore
                del binary_mask
                binary_mask = None
                
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
                    rect_tuple = cv2.minAreaRect(largest_contour)
                    box = cv2.boxPoints(rect_tuple)
                    quadrilateral = np.int0(box).reshape(-1, 1, 2)

                # Free contours
                del contours
                del largest_contour

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
                
                # Free intermediate arrays
                del pts, s, diff, quadrilateral

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
                
                # Free rect and dst
                del rect, dst

                # Apply perspective transformation
                original = cv2.imdecode(np.frombuffer(photo.body, np.uint8), cv2.IMREAD_COLOR)
                warped = cv2.warpPerspective(original, M, (final_width, final_height))
                
                # Free original and M
                del original, M
                original = None
                M = None

                is_success, buffer = cv2.imencode('.jpg', warped)
                
                # Free warped immediately after encoding
                del warped
                warped = None
                
                if is_success:
                    output_bytesio = io.BytesIO(buffer.tobytes())
                    # Free buffer
                    del buffer
                    buffer = None
                else:
                    raise ValueError(_("contour_failed"))

            except Exception as e:
                await message.reply(_("remove_background_failed")+f" {e}")
                logging.error(f"Error removing background: {e}")
                return
            finally:
                # Close photo_bytesio2
                if photo_bytesio:
                    photo_bytesio.close()
                    photo_bytesio = None
            
            # -------------------------------------------------------
            # Upload the processed image to S3 storage
            try:
                output_bytes = output_bytesio.getvalue()
                output_bytesio2 = io.BytesIO(output_bytes)
                cover_filename = f"{event_from_user.id}/cover/{uuid.uuid4()}.jpg" # Generate a unique filename for the photo
                await s3.upload_fileobj(output_bytesio2, com.AWS_BUCKET_NAME, cover_filename)
                await state.update_data(cover_filename=cover_filename) # Save the filename in the state
            except Exception as e:
                await message.reply(_("upload_failed")+f" {e}")
                logging.error(f"Error uploading to S3: {e}")
            finally:
                # Close output_bytesio2
                if output_bytesio2:
                    output_bytesio2.close()
                    output_bytesio2 = None
            
            # Remove temporal message
            if waiting_message:
                await waiting_message.delete()
                waiting_message = None

            # -------------------------------------------------------
            # Send the processed image back to the user
            keyboard = []
            for action in act.COVER_ACTIONS:
                keyboard.append(eng.CallbackButton(text=_(action), payload=env.CoverActions(action=action) ))
            output_bytes = output_bytesio.getvalue()
            sent_message = await eng.send_photo_from_bytes(event_chat.id, photo_bytes=output_bytes, filename=cover_filename)
            await eng.send_inline_keyboard(sent_message, keyboard, state)
            await state.set_state(env.State.wait_reaction_on_cover)
            
    finally:
        # Final cleanup - ensure all resources are freed
        if photo_bytesio:
            photo_bytesio.close()
        if output_bytesio:
            output_bytesio.close()
        if output_bytesio2:
            output_bytesio2.close()
        
        # Explicitly delete large numpy arrays
        del mask_np, mask_bw, binary_mask, kernel, original, warped, buffer

'''
# =========================================================
# Handler for inline button use_cover
@engt.base_router.callback_query(env.CoverActions.filter(F.action == "use_cover"))
async def use_cover(callback: CallbackQuery, callback_data: env.CoverActions, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
    await engt.RemoveInlineKeyboards(callback, state, bot, event_chat)
    # Give like to cover's photo
    await bot.set_message_reaction(chat_id=event_chat.id,
                                    message_id=callback.message.message_id,
                                    reaction=[ReactionTypeEmoji(emoji='👍')])
    await h_brief.AskForBrief(state, pool, bot, event_chat)

# =========================================================
# Handler for inline button use_original_photo
@engt.base_router.callback_query(env.CoverActions.filter(F.action == "use_original_photo"))
async def use_original_photo(callback: CallbackQuery, callback_data: env.CoverActions, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
    await engt.RemoveInlineKeyboards(callback, state, bot, event_chat)
    data = await state.get_data()
    photo_filename = data.get("photo_filename")
    await state.update_data(cover_filename=photo_filename) # Replace cover by original photo filename
    # Delete the message with the processed cover photo
    try:
        await bot.delete_message(chat_id=event_chat.id, message_id=callback.message.message_id)
    except Exception as e:
        engc.logging.warning(f"Failed to delete callback message: {e}")
    await h_brief.AskForBrief(state, pool, bot, event_chat)

# =========================================================
# Handler for inline button take_new_photo
@engt.base_router.callback_query(env.CoverActions.filter(F.action == "take_new_photo"))
async def take_new_cover_photo(callback: CallbackQuery, callback_data: env.CoverActions, state: FSMContext, pool: asyncpg.Pool, bot: Bot, event_chat: Chat) -> None:
    await engtRemoveInlineKeyboards(callback, state, bot, event_chat)
    await AskForCover(state, pool, bot, event_chat)
'''