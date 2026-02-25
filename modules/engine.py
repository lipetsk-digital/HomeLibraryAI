# Engine library to use aiogram and maxapi code in a unified way

import logging # For logging
import os # For environment variables
import datetime # For date and time
import aiohttp # For async HTTP requests
from dataclasses import dataclass # For data classes
from typing import Self # For type hinting of self return type
from enum import Enum, auto # For enumerations

from aiogram import Bot as Bot_tg
from maxapi import Bot as Bot_max

from aiogram import Dispatcher as Dispatcher_tg
from maxapi import Dispatcher as Dispatcher_max

from aiogram import Router as Router_tg
from maxapi import Router as Router_max

from modules.postgresstorage import PostgresStorage as PostgresStorage_tg
from modules.maxstorage import PostgresStorage as PostgresStorage_max

from aiogram.utils.i18n import I18n as I18n_tg
from aiogram.utils.i18n import FSMI18nMiddleware as FSMI18nMiddleware_tg

from aiogram.utils.i18n import gettext as gettext_tg
import gettext as gettext_max

from aiogram.types import BotCommand as BotCommand_tg
from maxapi.types.command import BotCommand as BotCommand_max

from aiogram.fsm.state import State as State_tg
from maxapi.context import State as State_max

from aiogram.fsm.state import StatesGroup as StatesGroup_tg
from maxapi.context import StatesGroup as StatesGroup_max

from aiogram.filters.command import Command as Command_tg
from maxapi.types import Command as Command_max

from aiogram.filters import CommandStart as CommandStart_tg
from maxapi.types import BotStarted as CommandStart_max

from aiogram.types import Chat as Chat_tg
from maxapi.types.chats import Chat as Chat_max

from aiogram.types import User as User_tg
from maxapi.types.users import User as User_max

from aiogram.types import Message as Message_tg
from maxapi.types.message import Message as Message_max
from maxapi.types import MessageCreated as MessageCreated_max

from maxapi.types.updates.update import Update as Update_max

from aiogram.filters.callback_data import CallbackData as CallbackData_tg
from maxapi.filters.callback_payload import CallbackPayload as CallbackData_max

from aiogram.utils.keyboard import InlineKeyboardBuilder as InlineKeyboardBuilder_tg
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder as InlineKeyboardBuilder_max

from maxapi.types import CallbackButton as CallbackButton_max

from aiogram.types.callback_query import CallbackQuery as CallbackQuery_tg
from maxapi.types import MessageCallback as CallbackQuery_max

from aiogram.fsm.context import FSMContext as FSMContext_tg
from modules.maxstorage import PostgresContext as PostgresContext_max

from aiogram import F as F_tg
from maxapi import F as F_max

from aiogram.enums.parse_mode import ParseMode as ParseMode_tg
from maxapi.enums.parse_mode import ParseMode as ParseMode_max

from aiogram.types import ReactionTypeEmoji as ReactionTypeEmoji_tg

from aiogram.types import BufferedInputFile as BufferedInputFile_tg
from maxapi.types import InputMediaBuffer as InputMediaBuffer_max

from maxapi.types import PhotoAttachmentPayload as PhotoAttachmentPayload_max
from maxapi.types import Attachment as Attachment_max
from maxapi.enums.attachment import AttachmentType as AttachmentType_max


# ========================================================
# Constants and settings
# ========================================================

HTTP_TIMEOUT_sec = 20 # Timeout for HTTP requests in seconds

# ========================================================
# Configuration data
# ========================================================

MESSENGER: bytes = None # Placeholder for messenger identifier: 'T' or 'M'
MESSENGER_TOKEN: str = None # Placeholder for messenger token
MESSENGER_PROXY: str = None # Placeholder for messenger token

# ========================================================
# Environment variables
# ========================================================

bot: Bot_tg | Bot_max = None  # Placeholder for bot instance
storage: PostgresStorage_tg | PostgresStorage_max = None  # Placeholder for storage instance
dp: Dispatcher_tg | Dispatcher_max = None  # Placeholder for dispatcher instance

only_user: int = 0 # Placeholder for only_user environment variable
exclude_user: int = 0 # Placeholder for exclude_user environment variable

first_router: Router_tg | Router_max = None # Router for global commands handlers
base_router: Router_tg | Router_max = None # Router for current situative handlers
last_router: Router_tg | Router_max = None # Router for trash messages

i18n: I18n_tg | gettext_max.GNUTranslations = None  # Placeholder for i18n instance (both telegram and max use aiogram.i18n)
FSMi18n: FSMI18nMiddleware_tg | None = None  # Placeholder for FSMi18n instance (telegram only)

StatesGroup: StatesGroup_tg | StatesGroup_max = None # Placeholder for StatesGroup class fabrique
ParseMode: ParseMode_tg | ParseMode_max = None # Placeholder for ParseMode type (telegram and max have different ParseMode classes, but we will use the same variable for both)

F = None # Placeholder for F magic filter constant

MaxBytesInButtonCaption: int = None # Placeholder for maximum bytes in button caption
MaxCharsInMessage: int = None # Placeholder for maximum characters in message
MaxButtonsInMessage: int = None # Placeholder for maximum buttons in message

# ========================================================
# Universal classes defenitions: see like telegram, bu works for max too
# You can add fields and methods as needed
# ========================================================

class User:
    """ Universal User class for both Telegram and MAX messengers."""
    id: int
    first_name: str
    last_name: str
    username: str
    def __init__(self, source=None):
        if isinstance(source, User_tg):
            # https://docs.aiogram.dev/en/dev-3.x/api/types/user.html
            self.id = source.id
            self.first_name = source.first_name
            self.last_name = source.last_name or ""
            self.username = source.username or ""
        elif isinstance(source, User_max):
            # https://love-apples.github.io/maxapi/types/users/#maxapi.types.users.User
            self.id = source.user_id
            self.first_name = source.first_name
            self.username = source.username or ""
            self.last_name = source.last_name or ""

class Chat:
    """ Universal Chat class for both Telegram and MAX messengers."""
    id: int
    title: str
    def __init__(self, source=None):
        if isinstance(source, Chat_tg):
            # https://docs.aiogram.dev/en/dev-3.x/api/types/chat.html
            self.id = source.id
            self.title = source.title or ""
        elif isinstance(source, Chat_max):
            # https://love-apples.github.io/maxapi/types/chats/#maxapi.types.chats.Chat
            self.id = source.chat_id
            self.title = source.title or ""
        elif isinstance(source, int):
            self.id = source
            self.title = ""

@dataclass
class Attachment():
    """ Universal Attachment class for both Telegram and MAX messengers"""
    body: bytes
    url: str
    token: str

class Message:
    """ Universal Message class for both Telegram and MAX messengers."""
    id: str
    date: datetime
    chat: Chat
    from_user: User
    text: str
    message_tg: Message_tg = None # Original Telegram message object, needed for editing messages in Telegram
    message_max: Message_max = None # Original MAX message object, needed for editing messages in MAX
    def __init__(self, source=None):
        if isinstance(source, Message_tg):
            # https://docs.aiogram.dev/en/dev-3.x/api/types/message.html
            self.id = str(source.message_id)
            self.date = source.date
            self.chat = Chat(source.chat)
            self.from_user = User(source.from_user) if source.from_user else None
            self.text = source.text
            self.message_tg = source
        elif isinstance(source, Message_max):
            # https://love-apples.github.io/maxapi/types/message/#maxapi.types.message.Message
            self.id = source.body.mid
            self.date = source.timestamp
            self.chat = Chat(source.recipient.chat_id) if source.recipient else None # Danger! Abstrace Max's Message does not have chat object, only recipient with chat_id
            self.from_user = User(source.sender) if source.sender else None
            self.text = source.body.text or "" if source.body else None
            self.message_max = source
        elif isinstance(source, MessageCreated_max):
            # https://love-apples.github.io/maxapi/types/message/#maxapi.types.message.Message
            self.id = source.message.body.mid
            self.date = source.message.timestamp
            self.chat = Chat(source.chat) if source.chat else None
            self.from_user = User(source.from_user) if source.from_user else None
            self.text = source.message.body.text or "" if source.message.body else None
            self.message_max = source.message
    async def delete(self):
        ''' Delete the message'''
        if MESSENGER == b'T':
            return await bot.delete_message(chat_id=self.chat.id, message_id=self.id)
        elif MESSENGER == b'M':
            return await bot.delete_message(message_id=self.id)
    async def reply(self, text: str, parse_mode: ParseMode_tg | ParseMode_max = None) -> Self:
        ''' Reply to the message with the given text and parse mode, and return the new message as a universal Message object.'''
        if MESSENGER == b'T':
            reply_message = await self.message_tg.reply(text=text, parse_mode=parse_mode)
            return self.__class__(reply_message)
        elif MESSENGER == b'M':
            sendedmessage = await self.message_max.reply(text=text, parse_mode=parse_mode)
            return self.__class__(sendedmessage.message)
    async def get_photo(self) -> Attachment:
        """ Get the photo bytes from the message."""
        if MESSENGER == b'T':
            try:
                photo = self.message_tg.photo[-1]
                photo_file = await bot.get_file(photo.file_id)
                photo_bytesio = await bot.download_file(photo_file.file_path)
                photo_bytes = photo_bytesio.read()
            finally: # Close photo_bytesio
                if photo_bytesio:
                    photo_bytesio.close()
                    photo_bytesio = None
            return Attachment(body=photo_bytes, url=photo_file.file_path, token=photo.file_id)
        elif MESSENGER == b'M':
            if self.message_max.body.attachments:
                if self.message_max.body.attachments[0].type != "image":
                    raise ValueError("The attachment is not a photo")
                photo_url = self.message_max.body.attachments[0].payload.url
                async with aiohttp.ClientSession() as session:
                    async with session.get(photo_url, timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT_sec)) as resp:
                        resp.raise_for_status()
                        photo_bytes = await resp.read()
                        return Attachment(body=photo_bytes, url=photo_url, token=self.message_max.body.attachments[0].payload.token)
            else:
                raise ValueError("No attachments found in the message")
    async def set_like(self) -> None:
        """ Set a like reaction to the message."""
        if MESSENGER == b'T':
            await bot.set_message_reaction(chat_id=self.chat.id,
                                            message_id=self.id,
                                            reaction=[ReactionTypeEmoji_tg(emoji='👍')])
        elif MESSENGER == b'M':
            pass; # MAX does not support reactions yet, so we will skip this step


CallbackData = CallbackData_tg | CallbackData_max

def CallbackData():
    """ Universal CallbackData class fabrique for both Telegram and MAX messengers."""
    if MESSENGER == b'T':
        return CallbackData_tg
    elif MESSENGER == b'M':
        return CallbackData_max

class CallbackButton:
    """ Universal CallbackButton class for both Telegram and MAX messengers."""
    text: str
    payload: CallbackData
    def __init__(self, text: str, payload: CallbackData_tg | CallbackData_max):
        self.text = text
        self.payload = payload

FSMContext = FSMContext_tg | PostgresContext_max

def State():
    """ Universal State class fabrique for both Telegram and MAX messengers."""
    if MESSENGER == b'T':
        return State_tg()
    elif MESSENGER == b'M':
        return State_max()
    
def Command(*args, **kwargs):
    """ Universal Command class fabrique for both Telegram and MAX messengers."""
    if MESSENGER == b'T':
        return Command_tg(*args, **kwargs)
    elif MESSENGER == b'M':
        return Command_max(*args, **kwargs)
    
class onButtonClick(Enum):
    RemoveKeyboardAndMessage = auto() # default
    RemoveKeyboardKeepMessage = auto()
    KeepKeyboardAndMessage = auto()

# ========================================================
# Bot startup routines definitions
# ========================================================

def init_bot(messenger: str, postgres_config: dict, _only_user: str = None, _exclude_user: str = None) -> None:
    """ Initialize bot, storage, dispatcher, and routers based on the selected messenger.
        
        Args:
            messenger (str): 'T' for Telegram, 'M' for MAX.
            postgres_config (dict): Configuration dictionary for PostgreSQL connection.
        For testing a bot without another developer key:
            only_user (str, optional): Only allow this user to interact with the bot. Defaults to None.
            exclude_user (str, optional): Exclude this user from interacting with the bot. Defaults to None.
    """
    if messenger not in ('T', 'M'):
        raise ValueError("Messenger must be 'T' or 'M'")
    
    global MESSENGER, MESSENGER_TOKEN, MESSENGER_PROXY
    global bot, storage, dp, StatesGroup, ParseMode, F
    global MaxBytesInButtonCaption, MaxCharsInMessage, MaxButtonsInMessage
    global only_user, exclude_user
    MESSENGER = messenger.encode('utf-8')

    only_user = int(_only_user) if _only_user else 0
    exclude_user = int(_exclude_user) if _exclude_user else 0

    if MESSENGER == b'T':
        MESSENGER_TOKEN = os.getenv("TELEGRAM_TOKEN")
        MESSENGER_PROXY = os.getenv("TELEGRAM_PROXY")
        bot = Bot_tg(token=MESSENGER_TOKEN, proxy=MESSENGER_PROXY)
        storage = PostgresStorage_tg(**postgres_config)
        dp = Dispatcher_tg(storage=storage)
        StatesGroup = StatesGroup_tg
        ParseMode = ParseMode_tg
        F = F_tg
        MaxBytesInButtonCaption = 64 # Telegram supports up to 64 bytes in callback data, but we need to reserve some bytes for the payload structure, so we will use 60 bytes for the actual data and 4 bytes for the structure. MAX supports up to 255 bytes in callback data, but we will use the same limit for consistency.
        MaxCharsInMessage = 4096 # Telegram supports up to 4096 characters in a message, but we will use 4000 characters for safety. MAX supports up to 2000 characters in a message, but we will use the same limit for consistency.
        MaxButtonsInMessage = 60 # Telegram supports up to 100 buttons in an inline keyboard, but 80+ buttons got REPLY_MARKUP_TOO_LONG error from Telegram

    elif MESSENGER == b'M':
        MESSENGER_TOKEN = os.getenv("MAX_TOKEN")
        bot = Bot_max(MESSENGER_TOKEN)
        postgres_storage = PostgresStorage_max(**postgres_config)
        storage = postgres_storage  # Alias for compatibility
        dp = Dispatcher_max(storage=PostgresContext_max, postgres_storage=postgres_storage)
        StatesGroup = StatesGroup_max
        ParseMode = ParseMode_max
        F = F_max
        MaxBytesInButtonCaption = 64 # Same limit in Telegram and Max
        MaxCharsInMessage = 4096 # It works both
        MaxButtonsInMessage = 30 # 30+ buttons got empty message in Max.

# -------------------------------------------------------
def init_router():
    """ Initialize routers based on the current messenger.
    """
    if MESSENGER == b'T':
        return Router_tg()
    elif MESSENGER == b'M':
        return Router_max()

# -------------------------------------------------------
def prepare_translator() -> None:
    """ Prepare i18n and FSMi18n middlewares based on the selected messenger.

        Telegram with autodetect locale for users.
        MAX with default locale 'ru'.
    """
    global i18n, FSMi18n
    if MESSENGER == b'T':
        i18n = I18n_tg(path="locales", default_locale="en", domain="messages")
        FSMi18n = FSMI18nMiddleware_tg(i18n=i18n).setup(dp)
    if MESSENGER == b'M':
        i18n = gettext_max.translation('messages', localedir='locales', languages=['ru'])
        
def _(*args, **kwargs):
    """ Universal gettext function for both Telegram and MAX messengers."""
    if MESSENGER == b'T':
        return gettext_tg(*args, **kwargs)
    elif MESSENGER == b'M':
        if len(args)+len(kwargs) <= 1:
            return i18n.gettext(*args, **kwargs)
        else:
            return i18n.ngettext(*args, **kwargs)
    
# -------------------------------------------------------
async def prepare_commands(actions: list) -> None:
    """ Prepare the bot's main menu commands

        Args:
            actions (list): List of action command string identifiers without slashes.
                            Commands descriptions will be translated by its id's by i18n.
        Example:
            prepare_commands( ['start', 'settings', 'help'] )
            will prepare commands /start, /settings, /help with descriptions: _('start'), _('settings'), _('help')
    """
    if MESSENGER == b'T':
        # Loop through all available languages and set the bot commands for each one    
        available_languages = i18n.available_locales
        logging.debug(f"Available languages: {available_languages}")
        for lang in available_languages:
            commands = []
            for action in actions:
                commands.append(BotCommand_tg(command=action, description=i18n.gettext(action, locale=lang)))
            await bot.set_my_commands(commands=commands, language_code=lang)

    elif MESSENGER == b'M':
        # MAX does not support per-language commands yet
        commands = []
        for action in actions:
            commands.append(BotCommand_max(name="/"+action, description=i18n.gettext(action)))
        await bot.set_my_commands(*commands)

# ========================================================
# Messages support
# ========================================================

async def send_message(chat_id: int, text: str, parse_mode: ParseMode_tg | ParseMode_max = None) -> Message:
    """ Send a message to the specified chat.

        Args:
            chat_id (int): The ID of the chat to send the message to.
            text (str): The text content of the message.

        Returns:
            Message: A universal Message object representing the sent message.
    """
    if MESSENGER == b'T':
        message = await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
        return Message(message)
    elif MESSENGER == b'M':
        sendedmessage = await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
        return Message(sendedmessage.message)

async def send_photo_from_bytes(chat_id: int, photo_bytes: bytes, filename: str, caption: str = None, parse_mode: ParseMode_tg | ParseMode_max = None) -> Message:
    """ Send a photo to the specified chat using raw bytes.

        Args:
            chat_id (int): The ID of the chat to send the photo to.
            photo_bytes (bytes): The raw bytes of the photo to be sent.
            filename (str): The filename to be used for the photo.
            caption (str): The caption for the photo (optional).

        Returns:
            Message: A universal Message object representing the sent message.
    """
    if MESSENGER == b'T':
        message = await bot.send_photo(chat_id=chat_id, photo=BufferedInputFile_tg(photo_bytes, filename=filename), caption=caption, parse_mode=parse_mode)
        return Message(message)
    elif MESSENGER == b'M':
        media = InputMediaBuffer_max(buffer=photo_bytes, filename=filename)
        sendedmessage = await bot.send_message(chat_id=chat_id, text=caption, attachments=[media], parse_mode=parse_mode)
        return Message(sendedmessage.message)

async def send_photo_from_token(chat_id: int, token: str, caption: str = None, parse_mode: ParseMode_tg | ParseMode_max = None) -> Message:
    """ Send a photo to the specified chat using a token.

        Args:
            chat_id (int): The ID of the chat to send the photo to.
            token (str): The token of the photo to be sent.
            caption (str): The caption for the photo (optional).

        Returns:
            Message: A universal Message object representing the sent message.
    """
    if MESSENGER == b'T':
        message = await bot.send_photo(chat_id=chat_id, photo=token, caption=caption, parse_mode=parse_mode)
        return Message(message)
    elif MESSENGER == b'M':
        #media = InputMedia_max(path=token)
        attachment = PhotoAttachmentPayload_max(photo_id=0, token=token, url="") # MAX does not support sending photos by token, but we can use the token to create a photo attachment payload and send it as an attachment
        media = Attachment_max(type=AttachmentType_max.IMAGE, payload=attachment)
        #media = Image_max(token=token)
        sendedmessage = await bot.send_message(chat_id=chat_id, text=caption, attachments=[media], parse_mode=parse_mode)
        return Message(sendedmessage.message)
    
# ========================================================
# Inline keyboards support
# ========================================================
async def send_inline_keyboard(message: Message, buttons: list[CallbackButton], state: FSMContext, row_width: int = 1, rule: onButtonClick = onButtonClick.RemoveKeyboardAndMessage) -> None:
    """ Send an inline keyboard with the given buttons.

        Args:
            message (Message): The message to which the inline keyboard will be attached.
            buttons (list[CallbackButton]): A list of CallbackButton instances to be included in the keyboard.
            row_width (int): The number of buttons per row in the keyboard (default is 1).
    """
    if MESSENGER == b'T':
        builder = InlineKeyboardBuilder_tg()
        for button in buttons:
            builder.button(text=button.text, callback_data=button.payload)
        builder.adjust(row_width)
        await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message.id, reply_markup=builder.as_markup())
    elif MESSENGER == b'M':
        builder = InlineKeyboardBuilder_max()
        counter = 0
        row = []
        for button in buttons:
            row.append(CallbackButton_max(text=button.text, payload=button.payload.pack()))
            counter += 1
            if counter >= row_width:
                builder.row(*row)
                row = []
                counter = 0
        if row: # add remaining buttons if they exist
            builder.row(*row)
        await bot.edit_message(message_id=message.id, attachments=(message.message_max.body.attachments + [builder.as_markup()]))
    # If the keyboard is not permanent, save the message ID in the FSM context to be able to delete it later
    if rule == onButtonClick.RemoveKeyboardAndMessage:
        data = await state.get_data()
        messages_to_remove = data.get("messages_to_remove", [])
        if isinstance(messages_to_remove, list):
            messages_to_remove.append(message.id)
        else:
            messages_to_remove = [message.id]
        await state.update_data(messages_to_remove=messages_to_remove)
    elif rule == onButtonClick.RemoveKeyboardKeepMessage:
        data = await state.get_data()
        keyboards_to_remove = data.get("keyboards_to_remove", [])
        if isinstance(keyboards_to_remove, list):
            keyboards_to_remove.append(message.id)
        else:
            keyboards_to_remove = [message.id]
        await state.update_data(keyboards_to_remove=keyboards_to_remove)

async def remove_temporary_inline_keyboards(chat_id: int, state: FSMContext) -> None:
    """ Remove all temporary inline keyboards by their message IDs stored in the FSM context.

        Args:
            chat_id (int): The ID of the chat where the messages with inline keyboards are located.
            state (FSMContext): The FSM context where the message IDs of inline keyboards are stored.
    """
    data = await state.get_data()
    messages_to_remove = data.get("messages_to_remove", [])
    if isinstance(messages_to_remove, list):
        for message_id in messages_to_remove:
            try:
                if MESSENGER == b'T':
                    await bot.delete_message(chat_id=chat_id, message_id=message_id)
                elif MESSENGER == b'M':
                    await bot.delete_message(message_id=message_id)
            except Exception as e:
                logging.warning(f"Failed to remove inline keyboard from message {message_id}: {e}")
        await state.update_data(messages_to_remove=[])
    keyboards_to_remove = data.get("keyboards_to_remove", [])
    if isinstance(keyboards_to_remove, list):
        for message_id in keyboards_to_remove:
            try:
                if MESSENGER == b'T':
                    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
                elif MESSENGER == b'M':
                    message_max = await bot.get_message(message_id=message_id)
                    attachments_new = []
                    for attachment in message_max.body.attachments:
                        if attachment.type != "inline_keyboard":
                            attachments_new.append(attachment)
                    await bot.edit_message(message_id=message_id, attachments=attachments_new)
            except Exception as e:
                logging.warning(f"Failed to remove inline keyboard from message {message_id}: {e}")
        await state.update_data(keyboards_to_remove=[])

# ========================================================
# Decorators of message handlers
# ========================================================

def F_text():
    """ Universal F.text magic filter constant for both Telegram and MAX messengers."""
    if MESSENGER == b'T':
        return F_tg.text
    elif MESSENGER == b'M':
        return F_max.message.body.text
    
def F_photo():
    """ Universal F.photo magic filter constant for both Telegram and MAX messengers.
        For MAX-messenger returns True if the message contains attachments (photos), False otherwise.
    """
    if MESSENGER == b'T':
        return F_tg.photo
    elif MESSENGER == b'M':
        return F_max.message.body.attachments

def message_handler(func):
    """ Universal message handler decorator for both Telegram and MAX messengers."""
    if MESSENGER == b'T':
        async def wrapper_tg(message: Message_tg, state: FSMContext_tg, event_chat: Chat_tg, event_from_user: User_tg):
            if only_user != 0:
                if event_from_user.id != only_user:
                    return
            if exclude_user != 0:
                if event_from_user.id == exclude_user:
                    return
            await remove_temporary_inline_keyboards(event_chat.id, state)
            return await func(message=Message(message), state=state, event_chat=Chat(event_chat), event_from_user=User(event_from_user))
        return wrapper_tg
    elif MESSENGER == b'M':
        async def wrapper_max(event: Update_max, context: PostgresContext_max):
            if only_user != 0:
                if event.from_user.user_id != only_user:
                    return
            if exclude_user != 0:
                if event.from_user.user_id == exclude_user:
                    return
            if isinstance(event, CommandStart_max):
                await remove_temporary_inline_keyboards(event.chat_id, context)
                return await func(message=None, state=context, event_chat=Chat(event.chat_id), event_from_user=User(event.from_user))
            elif isinstance(event, MessageCreated_max):
                await remove_temporary_inline_keyboards(event.message.recipient.chat_id, context)
                return await func(message=Message(event.message), state=context, event_chat=Chat(event.message.recipient.chat_id), event_from_user=User(event.from_user))
        return wrapper_max

def on_start_conversation(router: any):
    """ Universal decorator for handling the start of a conversation with the bot for both Telegram and MAX messengers."""
    if MESSENGER == b'T':
        def decorator(func):
            return router.message(CommandStart_tg())(func)
        return decorator
    elif MESSENGER == b'M':
        def decorator(func):
            return router.bot_started()(func)
        return decorator
    
def on_message(router: any, *args):
    """ Universal decorator for handling messages for both Telegram and MAX messengers."""
    if MESSENGER == b'T':
        def decorator(func):
            return router.message(*args)(func)
        return decorator
    elif MESSENGER == b'M':
        def decorator(func):
            return router.message_created(*args)(func)
        return decorator

# ========================================================
# Decorators of callback handlers
# ========================================================
def callback_handler(func):
    """ Universal callback query handler decorator for both Telegram and MAX messengers."""
    if MESSENGER == b'T':
        async def wrapper_tg(callback: CallbackQuery_tg, callback_data: CallbackData_tg, state: FSMContext_tg, event_chat: Chat_tg, event_from_user: User_tg):
            if only_user != 0:
                if event_from_user.id != only_user:
                    return
            if exclude_user != 0:
                if event_from_user.id == exclude_user:
                    return
            await remove_temporary_inline_keyboards(event_chat.id, state)
            return await func(message=Message(callback.message), callback=callback_data, state=state, event_chat=Chat(event_chat), event_from_user=User(event_from_user))
        return wrapper_tg
    elif MESSENGER == b'M':
        async def wrapper_max(event: CallbackQuery_max, payload: CallbackData_tg | CallbackData_max, context: PostgresContext_max):
            if only_user != 0:
                if event.callback.user.user_id != only_user:
                    return
            if exclude_user != 0:
                if event.callback.user.user_id == exclude_user:
                    return
            await remove_temporary_inline_keyboards(event.message.recipient.chat_id, context)
            return await func(message=Message(event.message), callback=payload, state=context, event_chat=Chat(event.message.recipient.chat_id), event_from_user=User(event.callback.user))
        return wrapper_max

def on_callback(router: any, *args):
    """ Universal decorator for handling callback queries for both Telegram and MAX messengers."""
    if MESSENGER == b'T':
        def decorator(func):
            return router.callback_query(*args)(func)
        return decorator
    elif MESSENGER == b'M':
        def decorator(func):
            return router.message_callback(*args)(func)
        return decorator