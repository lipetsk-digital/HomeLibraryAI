import asyncpg # For asynchronous PostgreSQL connection
from aiogram import Bot, Dispatcher # For Telegram bot framework
from aiogram.utils.i18n import I18n, FSMI18nMiddleware # For internationalization and localization

# Internal modules
import modules.engine as eng # For basic engine functions and definitions
import modules.environment as env # For environment variables and configurations
from modules.postgresstorage import PostgresStorage # For PostgreSQL storage of bot state
import modules.database as database # For creating tables in PostgreSQL
import modules.book as book # For books routines

# Handler modules (imported to register their routes via decorators)
import modules.h_start as h_start # For handling start command
import modules.h_menu as h_menu # For handling main menu commands
import modules.h_cat as h_cat # For manipulating cathegories
import modules.h_cover as h_cover # For handling book cover photos
import modules.h_brief as h_brief # For handling brief commands
import modules.h_edit as h_edit # For handling book editing
import modules.h_search as h_search # For handling book search
import modules.h_lang as h_lang # For handling language selection

# Initialize bot and dispatcher
bot = Bot(token=eng.TELEGRAM_TOKEN, proxy=eng.TELEGRAM_PROXY)
storage = PostgresStorage(**eng.POSTGRES_CONFIG)
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
    try:
        # Create a Postgres database connection pool
        eng.pool = await asyncpg.create_pool(**eng.POSTGRES_CONFIG)
        
        # Add middleware for database access
        dp.update.middleware(DatabaseMiddleware(eng.pool))

        # Add middleware for internationalization
        eng.i18n = I18n(path="locales", default_locale="en", domain="messages")
        eng.FSMi18n = FSMI18nMiddleware(i18n=eng.i18n).setup(dp)

        # Table creation (if not exists)
        await database.create_tables(eng.POSTGRES_CONFIG)
        
        # Register handlers
        dp.include_router(eng.first_router) # Global commands
        dp.include_router(eng.base_router)  # Base handlers
        dp.include_router(eng.last_router) # Trash messages
        
        # Register startup routines
        dp.startup.register(h_start.PrepareGlobalMenu)

        # Start bot polling
        await dp.start_polling(bot)
    finally:
        # Close database connection pool
        if eng.pool:
            await eng.pool.close()

# Run the bot in global thread
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())