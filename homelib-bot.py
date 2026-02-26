import os # For environment variables
import logging # For logging

import modules.database as db # For database functions and definitions
import modules.engine as eng # For crossplatform bot engine functions and definitions
import modules.actions as act # For bot commands and actions

# Prepare logging
logging.basicConfig(level=logging.INFO)

# Initialize bot
eng.init_bot(os.getenv("MESSENGER"), db.POSTGRES_CONFIG, os.getenv("ONLY_USER"), os.getenv("EXCLUDE_USER"))

# Initialize routers
eng.first_router = eng.init_router()
eng.base_router = eng.init_router()
eng.last_router = eng.init_router()

# Start the bot
async def main():
    try:
        # Messenger table creation (if not exists)
        await eng.storage.init()

        # Prepare multilingual support
        eng.prepare_translator()

        # Import events handlers
        import modules.h_start as h_start # For start handlers
        import modules.h_menu as h_menu # For main menu handlers
        import modules.h_cat as h_cat # For category selection handlers
        import modules.h_cover as h_cover # For book cover photo handlers
        import modules.h_search as h_search # For book search handlers
        import modules.h_cover as h_cover # For book brief photo handlers
        import modules.h_brief as h_brief # For book brief photo handlers
        import modules.h_lang as h_lang # For language selection handlers

        # Register routers handlers
        eng.dp.include_routers(eng.first_router, eng.base_router, eng.last_router)

        # Prepare bot commands menu
        await eng.prepare_commands(actions=(act.MAIN_MENU_ACTIONS + act.ADVANCED_ACTIONS))

        # Books table creation (if not exists)
        await db.init()

        # Start bot polling
        await eng.dp.start_polling(eng.bot)
    finally:
        # Close database connection pool
        if db.pool:
            await db.pool.close()

# Run the bot in global thread
if __name__ == '__main__':
    import asyncio
    asyncio.run(main())