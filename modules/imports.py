# Unified module for all imports used in the project

import asyncpg # For asynchronous PostgreSQL connection
import aioboto3 # For AWS S3 storage
from openai import AsyncOpenAI # For OpenAI API client
import cv2 # For image processing
from modules.aiorembg import async_remove # For asynchronous background removal

import io # For handling byte streams
import uuid # For generating unique filenames
import base64 # For encoding and decoding base64
import random # For random choices
import numpy as np # For arrays processing
from aiogram.utils.i18n import gettext as _ # For internationalization and localization
from babel import Locale # For locale handling
from aiogram.utils.formatting import Text, as_list, as_key_value # For formatting messages

from aiogram import Bot # For Telegram bot framework
from aiogram import Router # For creating a router for handling messages
from aiogram import F # For Telegram bot framework filters
from aiogram.types import Chat # For Telegram chat handling
from aiogram.types import User # For Telegram user handling
from aiogram.types import Message # For Telegram message handling
from aiogram.types import ReactionTypeEmoji # For Telegram message reactions
from aiogram.types import BufferedInputFile # For send images to user
from aiogram.filters.command import Command # For command handling
from aiogram.utils.keyboard import InlineKeyboardBuilder # For creating inline keyboards
from aiogram.types.callback_query import CallbackQuery # For handling callback queries
from aiogram.filters.callback_data import CallbackData # For callback data handling
from aiogram.fsm.context import FSMContext # For finite state machine context
from aiogram.fsm.state import State, StatesGroup # For finite state machine of Telegram-bot

import modules.environment as env # For bot configurations
import modules.engine as eng # For basic engine functions and defenitions

