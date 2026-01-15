import asyncpg # For asynchronous PostgreSQL connection
from aiohttp import web # For web server
import ssl # For SSL context
import asyncio # For async operations

# Internal modules
import modules.engine as eng # For basic engine functions and definitions
import modules.database as database # For creating tables in PostgreSQL
import modules.book as book # For books routines

# Middleware для редиректа с HTTP на HTTPS
@web.middleware
async def redirect_to_https(request, handler):
    # Если это HTTP-запрос, перенаправляем на HTTPS
    if request.scheme == 'http':
        https_url = request.url.with_scheme('https').with_port(eng.HTTPS_PORT)
        return web.HTTPMovedPermanently(https_url)
    return await handler(request)

# Start the server
async def main():
    
    # ------------ Database initialization ------------
    # Create a Postgres database connection pool
    eng.pool = await asyncpg.create_pool(**eng.POSTGRES_CONFIG)
    
    # Table creation (if not exists)
    await database.create_tables(eng.POSTGRES_CONFIG)    

    # ------------ HTTP server initialization ------------
    # Create HTTP app with redirect middleware
    http_app = web.Application(middlewares=[redirect_to_https])
    http_app.router.add_route('*', '/{path:.*}', lambda request: None)  # Catch all routes

    # Start HTTP redirect server
    http_runner = web.AppRunner(http_app)
    await http_runner.setup()
    http_site = web.TCPSite(http_runner, port=eng.HTTP_PORT)
    await http_site.start()
    print(f"HTTP redirect server started on port {eng.HTTP_PORT}")
    
    # ------------ HTTPS server initialization ------------
    # Create web application for HTTPS
    https_app = web.Application()

    # Setup web-server routes
    https_app.router.add_get('/', lambda request: web.FileResponse('web/index.html')) # Main page
    https_app.router.add_get('/lib/{user}', book.library_html) # Users libraries pages
    https_app.router.add_static('/', path='web', follow_symlinks=False, show_index=False) # Static files

    # Start HTTPS server
    https_runner = web.AppRunner(https_app)
    await https_runner.setup()
    
    # Setup SSL context for HTTPS
    ssl_context = None
    if eng.SSL_CERT_PATH and eng.SSL_KEY_PATH:
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(eng.SSL_CERT_PATH, eng.SSL_KEY_PATH)

    if ssl_context:
        https_site = web.TCPSite(https_runner, port=eng.HTTPS_PORT, ssl_context=ssl_context)
        await https_site.start()
        print(f"HTTPS server started on port {eng.HTTPS_PORT}")
    else:
        print("Warning: SSL certificates not configured, HTTPS server not started")
    
    # ------------ Main loop ------------
    # Keep server running
    try:
        await asyncio.Event().wait() # Run forever
    finally:
        await https_runner.cleanup()
        await http_runner.cleanup()
        await eng.pool.close()
    
# Run the bot in global thread
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())