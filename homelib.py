import asyncpg # For asynchronous PostgreSQL connection
from aiogram import Bot, Dispatcher # For Telegram bot framework
from aiogram.utils.i18n import I18n, FSMI18nMiddleware # For internationalization and localization

# Internal modules
import modules.engine as eng # For basic engine functions and definitions
import modules.environment as env # For environment variables and configurations
from modules.postgresstorage import PostgresStorage # For PostgreSQL storage of bot state
import modules.database as database # For creating tables in PostgreSQL
import modules.h_start as h_start # For handling start command
import modules.h_add as h_add # For handling adding a new book
#import modules.h_cat as h_cat # For manipulating cathegories
#import modules.h_lang as h_lang # For handling language selection
#import modules.h_cover as h_cover # For handling book cover photos
#import modules.h_brief as h_brief # For handling brief commands
#import modules.h_next as h_next # For handling next book commands
#import modules.h_field as h_field # For handling field selection
#import modules.h_edit as h_edit # For handling book editing
#import modules.h_search as h_search # For handling book search
#import modules.h_rename as h_rename # For handling category renaming
#import modules.h_history as h_history # For handling book history

# Initialize bot and dispatcher
bot = Bot(token=eng.TELEGRAM_TOKEN)
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
    # Create a Postgres database connection pool
    pool = await asyncpg.create_pool(**eng.POSTGRES_CONFIG)
    
    # Add middleware for database access
    dp.update.middleware(DatabaseMiddleware(pool))

    # Add middleware for internationalization
    eng.i18n = I18n(path="locales", default_locale="en", domain="messages")
    eng.FSMi18n = FSMI18nMiddleware(i18n=eng.i18n).setup(dp)

    # Table creation (if not exists)
    await database.create_tables(eng.POSTGRES_CONFIG)
    
    # Register handlers
    dp.include_router(eng.first_router) # Global commands
    #dp.include_router(h_add.add_router)
    #dp.include_router(h_cat.cat_router)
    #dp.include_router(h_lang.lang_router)
    #dp.include_router(h_cover.cover_router)
    #dp.include_router(h_brief.brief_router)
    #dp.include_router(h_next.next_router)
    #dp.include_router(h_field.field_router)
    #dp.include_router(h_edit.edit_router)
    #dp.include_router(h_search.search_router)
    #dp.include_router(h_rename.rename_router)
    dp.include_router(eng.last_router) # Trash messages
    
    # Register startup routines
    dp.startup.register(eng.PrepareGlobalMenu)

    # Start bot polling
    await dp.start_polling(bot)

# Run the bot in global thread
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())