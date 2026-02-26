import asyncio
import logging
import os
from typing import Optional, Any

from aiohttp import web
from rembg import remove, new_session

# ========================================================
# Configuration
# ========================================================
HOST = os.getenv("REMBG_HOST", "0.0.0.0")
PORT = int(os.getenv("REMBG_PORT", "80"))
MODEL = os.getenv("REMBG_MODEL", "birefnet-general")
MAX_CONTENT_LENGTH = int(os.getenv("REMBG_MAX_SIZE", str(50 * 1024 * 1024)))  # 50 MB

# ========================================================
# Logging
# ========================================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("rembg-service")

# ========================================================
# Session & queue management
# ========================================================
_session_hq = None

def get_session():
    """Get or create rembg session (lazy initialization)"""
    global _session_hq
    if _session_hq is None:
        log.info("Initializing rembg session with model '%s' ...", MODEL)
        _session_hq = new_session(MODEL)
        log.info("Session ready.")
    return _session_hq

# Semaphore to limit concurrent rembg operations to 1
_rembg_semaphore = asyncio.Semaphore(1)

# Counter for tracking queue position
_queue_counter = 0
_queue_lock = asyncio.Lock()

async def get_queue_size() -> int:
    async with _queue_lock:
        return _queue_counter

async def async_remove(input_data: bytes, executor: Optional[Any] = None, **kwargs) -> bytes:
    """Asynchronous wrapper for rembg.remove with queue management"""
    async with _queue_lock:
        global _queue_counter
        _queue_counter += 1
    try:
        async with _rembg_semaphore:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                executor,
                lambda: remove(input_data, **kwargs)
            )
            return result
    finally:
        async with _queue_lock:
            _queue_counter -= 1

# ========================================================
# HTTP handlers
# ========================================================

async def handle_remove(request: web.Request) -> web.Response:
    """POST /remove — remove background from image.
    
    Query params (optional):
        only_mask=true  — return only the mask instead of the full result
    
    Request body: raw image bytes (Content-Type: application/octet-stream or image/*)
    Response: processed image bytes (image/png)
    """
    # Read body
    body = await request.read()
    if not body:
        return web.Response(status=400, text="Empty request body")
    if len(body) > MAX_CONTENT_LENGTH:
        return web.Response(status=413, text="Payload too large")

    only_mask = request.query.get("only_mask", "").lower() in ("true", "1", "yes")
    
    log.info("Remove request: %d bytes, only_mask=%s", len(body), only_mask)

    try:
        result = await async_remove(
            body,
            session=get_session(),
            only_mask=only_mask,
        )
        return web.Response(
            body=result,
            content_type="image/png",
        )
    except Exception as e:
        log.exception("Error processing image")
        return web.Response(status=500, text=str(e))


async def handle_queue(request: web.Request) -> web.Response:
    """GET /queue — return current queue size as JSON."""
    size = await get_queue_size()
    return web.json_response({"queue_size": size})


async def handle_health(request: web.Request) -> web.Response:
    """GET /health — simple health check."""
    return web.json_response({"status": "ok"})


# ========================================================
# App factory & startup
# ========================================================

def create_app() -> web.Application:
    app = web.Application(client_max_size=MAX_CONTENT_LENGTH)
    app.router.add_post("/remove", handle_remove)
    app.router.add_get("/queue", handle_queue)
    app.router.add_get("/health", handle_health)
    return app


if __name__ == "__main__":
    log.info("Starting rembg service on %s:%d (model=%s)", HOST, PORT, MODEL)
    app = create_app()
    web.run_app(app, host=HOST, port=PORT)
