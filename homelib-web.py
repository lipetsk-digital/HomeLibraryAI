import asyncpg # For asynchronous PostgreSQL connection
from aiohttp import web # For web server

# Internal modules
import modules.engine as eng # For basic engine functions and definitions
import modules.database as database # For creating tables in PostgreSQL
import modules.book as book # For books routines

# Start the bot
async def main():
    
    # Create web application
    web_app = web.Application()

    # Create a Postgres database connection pool
    eng.pool = await asyncpg.create_pool(**eng.POSTGRES_CONFIG)
    
    # Table creation (if not exists)
    await database.create_tables(eng.POSTGRES_CONFIG)    

    # Setup web-server routes
    web_app.router.add_get('/', lambda request: web.FileResponse('web/index.html')) # Main page
    web_app.router.add_get('/lib/{user}', book.library_html) # Users libraries pages
    web_app.router.add_static('/', path='web', follow_symlinks=False, show_index=False) # Static files

    # Start web server
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, port=eng.WEB_PORT)
    await site.start()
    print(f"Web server started on port {eng.WEB_PORT}")
    
    # Keep server running
    try:
        await asyncio.Event().wait()  # Блокировка навсегда
    finally:
        await runner.cleanup()
        await eng.pool.close()
    
# Run the bot in global thread
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())