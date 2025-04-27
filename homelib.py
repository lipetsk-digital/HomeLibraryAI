import os
import logging
import asyncpg
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# PostgreSQL connection settings
POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "database": os.getenv("POSTGRES_DATABASE"),
    "user": os.getenv("POSTGRES_USERNAME"),
    "password": os.getenv("POSTGRES_PASSWORD")
}

# Logging configuration
logging.basicConfig(level=logging.INFO)

# Telegram bot token
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Class for finite state machine
class Form(StatesGroup):
    first_name = State()
    last_name = State()
    position = State()


# Create tables in PostgreSQL if they doesn't exist
async def create_tables():
    conn = await asyncpg.connect(**POSTGRES_CONFIG)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            userid BIGINT,
            nickname TEXT,
            username TEXT,
            datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS state (
            userid BIGINT PRIMARY KEY,
            state TEXT,
            cathegory TEXT,
            uidphoto UUID,
            uidcover UUID,
            uidannotation UUID,
            bookid BIGINT,
            cathegorytask TEXT,
            name TEXT,
            authors TEXT,
            pages TEXT,
            puiblisher TEXT,
            year TEXT,
            isbn TEXT,
            annotation TEXT,
            brief TEXT           
        )
    ''')
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS books (
            userid BIGINT,
            bookid BIGINT,
            cathegory TEXT,
            uidphoto UUID,
            uidcover UUID,
            uidannotation UUID,
            name TEXT,
            authors TEXT,
            pages TEXT,
            puiblisher TEXT,
            year TEXT,
            isbn TEXT,
            annotation TEXT,
            brief TEXT,
            datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (userid, bookid)
        )
    ''')
    await conn.close()

# Configuring middleware for database access
class DatabaseMiddleware:
    def __init__(self, pool):
        self.pool = pool

    async def __call__(self, handler, event, data):
        data['pool'] = self.pool
        return await handler(event, data)

# Обработчик всех команд
@dp.message()
async def doitall(message: types.Message, state: FSMContext, pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO logs (userid, nickname, username) VALUES ($1, $2, $3)",
            message.from_user.id, message.from_user.username, message.from_user.full_name
        )
    await message.answer("I remember you! 😉")

# Start the bot
async def main():
    # Create a connection pool
    pool = await asyncpg.create_pool(**POSTGRES_CONFIG)
    
    # Add middleware for database access
    dp.update.middleware(DatabaseMiddleware(pool))
    
    # Table creation (if not exists)
    await create_tables()
    
    # Start polling
    await dp.start_polling(bot)

# Run the bot in global thread
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())