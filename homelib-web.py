import asyncpg # For asynchronous PostgreSQL connection
from aiohttp import web # For web server
import asyncio # For async operations

# Internal modules
import modules.database as db # For creating tables in PostgreSQL
import modules.web as wb # For web engine functions and definitions
import modules.book_web as book # For books routines

# Start the server
async def main():
    
    # ------------ Database initialization ------------
    # Create a Postgres database connection pool
    db.pool = await asyncpg.create_pool(**db.POSTGRES_CONFIG)
    
    # Table creation (if not exists)
    await db.create_tables(db.POSTGRES_CONFIG)    

    # ------------ HTTP server initialization ------------
    # Create HTTP app with redirect middleware
    http_app = web.Application()
    http_app.router.add_get('/', lambda request: web.FileResponse('web/index.html')) # Main page
    http_app.router.add_get('/lib/{user}', book.library_html) # Users libraries pages
    http_app.router.add_static('/', path='web', follow_symlinks=False, show_index=False) # Static files

    # Start HTTP redirect server
    http_runner = web.AppRunner(http_app)
    await http_runner.setup()
    http_site = web.TCPSite(http_runner, port=wb.HTTP_PORT)
    await http_site.start()
    print(f"HTTP server started on port {wb.HTTP_PORT}")
    
    # ------------ Main loop ------------
    # Keep server running
    try:
        await asyncio.Event().wait() # Run forever
    finally:
        await http_runner.cleanup()
        await db.pool.close()
    
# Run the bot in global thread
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())