# Engine library to use aiogram and maxapi code in a unified way

import logging # For logging
import os # For environment variables
import datetime # For date and time
from typing import Protocol # For define typical class interfaces

from aiogram import Bot as Bot_tg
from maxapi import Bot as Bot_max

from aiogram import Dispatcher as Dispatcher_tg
from modules.maxstorage import PostgresDispatcher as Dispatcher_max

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
from maxapi.types import BotStarted as BotStarted_max

from aiogram.types import Chat as Chat_tg
from maxapi.types.chats import Chat as Chat_max

from aiogram.types import User as User_tg
from maxapi.types.users import User as User_max

from aiogram.types import Message as Message_tg
from maxapi.types.message import Message as Message_max
from maxapi.types import MessageCreated as MessageCreated_max

from maxapi.types.updates.update import Update as Update_max

from aiogram.fsm.context import FSMContext as FSMContext_tg
from modules.maxstorage import PostgresContext as PostgresContext_max

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

first_router: Router_tg | Router_max = None # Router for global commands handlers
base_router: Router_tg | Router_max = None # Router for current situative handlers
last_router: Router_tg | Router_max = None # Router for trash messages

i18n: I18n_tg | gettext_max.GNUTranslations = None  # Placeholder for i18n instance (both telegram and max use aiogram.i18n)
FSMi18n: FSMI18nMiddleware_tg | None = None  # Placeholder for FSMi18n instance (telegram only)

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

class Message:
    """ Universal Message class for both Telegram and MAX messengers."""
    id: str
    date: datetime
    chat: Chat
    from_user: User
    text: str
    def __init__(self, source=None):
        if isinstance(source, Message_tg):
            # https://docs.aiogram.dev/en/dev-3.x/api/types/message.html
            self.id = str(source.message_id)
            self.date = source.date
            self.chat = Chat(source.chat)
            self.from_user = User(source.from_user) if source.from_user else None
            self.text = source.text
        elif isinstance(source, Message_max):
            # https://love-apples.github.io/maxapi/types/message/#maxapi.types.message.Message
            self.id = source.body.mid
            self.date = source.timestamp
            self.chat = Chat(source.recipient.chat_id) if source.recipient else None # Danger! Abstrace Max's Message does not have chat object, only recipient with chat_id
            self.from_user = User(source.sender) if source.sender else None
            self.text = source.body.text or "" if source.body else None
        elif isinstance(source, MessageCreated_max):
            # https://love-apples.github.io/maxapi/types/message/#maxapi.types.message.Message
            self.id = source.message.body.mid
            self.date = source.message.timestamp
            self.chat = Chat(source.chat) if source.chat else None
            self.from_user = User(source.from_user) if source.from_user else None
            self.text = source.message.body.text or "" if source.message.body else None

class CallbackQuery:
    """ Universal CallbackQuery class for both Telegram and MAX messengers."""
    message: Message
    data: str
    from_user: User
    id: str

class FSMContext(Protocol):
    """ Protocol class for FSMContext to define typical methods used in both telegram and maxapi contexts."""
    async def get_data(self) -> dict[str, any]:
        pass
    async def update_data(self, **kwargs) -> None:
        pass
    async def get_state(self) -> State_tg | State_max | None:
        pass
    async def set_state(self, state: State_tg | State_max | None) -> None:
        pass

# ========================================================
# Routines defenitions
# ========================================================

def init_bot(messenger: str, postgres_config: dict) -> None:
    """ Initialize bot, storage, dispatcher, and routers based on the selected messenger.
        
        Args:
            messenger (str): 'T' for Telegram, 'M' for MAX.
            postgres_config (dict): Configuration dictionary for PostgreSQL connection.
    """
    if messenger not in ('T', 'M'):
        raise ValueError("Messenger must be 'T' or 'M'")
    
    global MESSENGER, MESSENGER_TOKEN, MESSENGER_PROXY
    global bot, storage, dp
    MESSENGER = messenger.encode('utf-8')

    if MESSENGER == b'T':
        MESSENGER_TOKEN = os.getenv("TELEGRAM_TOKEN")
        MESSENGER_PROXY = os.getenv("TELEGRAM_PROXY")
        bot = Bot_tg(token=MESSENGER_TOKEN, proxy=MESSENGER_PROXY)
        storage = PostgresStorage_tg(**postgres_config)
        dp = Dispatcher_tg(storage=storage)

    elif MESSENGER == b'M':
        MESSENGER_TOKEN = os.getenv("MAX_TOKEN")
        bot = Bot_max(MESSENGER_TOKEN)
        storage = PostgresStorage_max(**postgres_config)
        dp = Dispatcher_max(storage=storage)

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
        return i18n.gettext(*args, **kwargs)
    
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
# Basic decorators defenitions
# ========================================================
def message_handler(func):
    if MESSENGER == b'T':
        async def wrapper_tg(message: Message_tg, state: FSMContext_tg, event_chat: Chat_tg, event_from_user: User_tg):
            return await func(message=Message(message), callback=None, state=state, event_chat=Chat(event_chat), event_from_user=User(event_from_user))
        return wrapper_tg
    elif MESSENGER == b'M':
        async def wrapper_max(event: Update_max, context: PostgresContext_max):
            return await func(message=Message(event), callback=None, state=context, event_chat=Chat(event.chat), event_from_user=User(event.from_user))
        return wrapper_max

def on_start_conversation(router: any):
    if MESSENGER == b'T':
        def decorator(func):
            return router.message(CommandStart_tg())(func)
        return decorator
    elif MESSENGER == b'M':
        def decorator(func):
            return router.bot_started()(func)
        return decorator

def on_message(router: any):
    if MESSENGER == b'T':
        def decorator(func):
            return router.message()(func)
        return decorator
    elif MESSENGER == b'M':
        def decorator(func):
            return router.message_created()(func)
        return decorator

