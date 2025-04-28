import asyncpg # For asynchronous PostgreSQL connection
# For Telegram bot framework
from aiogram import Bot, Dispatcher
#from aiogram.fsm.storage.memory import MemoryStorage

# Internal modules
import modules.environment as env # For environment variables and configurations
import modules.databasecreation as databasecreation # For creating tables in PostgreSQL
from modules.handle_addbook import addbook_router # For handling messages related to adding books
from modules.postgres_storage import PostgresStorage # For PostgreSQL storage of bot state

# Initialize bot and dispatcher
bot = Bot(token=env.TOKEN)
#storage = MemoryStorage()
storage = PostgresStorage(**env.POSTGRES_CONFIG)
dp = Dispatcher(storage=storage)

# Configuring middleware for database access
class DatabaseMiddleware:
    def __init__(self, pool):
        self.pool = pool

    async def __call__(self, handler, event, data):
        data['pool'] = self.pool
        return await handler(event, data)

# Start the bot
async def main():
    # Create a Postgres database connection pool
    pool = await asyncpg.create_pool(**env.POSTGRES_CONFIG)
    
    # Add middleware for database access
    dp.update.middleware(DatabaseMiddleware(pool))
    
    # Table creation (if not exists)
    await databasecreation.create_tables(env.POSTGRES_CONFIG)
    
    # Register handlers
    dp.include_router(addbook_router)

    # Start bot polling
    await dp.start_polling(bot)

# Run the bot in global thread
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())