import asyncpg # For asynchronous PostgreSQL connection
from aiogram import Bot, Dispatcher # For Telegram bot framework

# Internal modules
import modules.environment as env # For environment variables and configurations
from modules.postgres_storage import PostgresStorage # For PostgreSQL storage of bot state
import modules.database_creation as database_creation # For creating tables in PostgreSQL
import modules.h_start as h_start # For handling start command
import modules.h_add as h_add # For handling adding a new book
import modules.h_cat as h_cat # For manipulating cathegories

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
    await database_creation.create_tables(env.POSTGRES_CONFIG)
    
    # Register handlers
    dp.include_router(h_start.start_router)
    dp.include_router(h_add.add_router)
    dp.include_router(h_cat.cat_router)
    
    # Register startup routines
    dp.startup.register(h_start.PrepareMenu)

    # Start bot polling
    await dp.start_polling(bot)

# Run the bot in global thread
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())