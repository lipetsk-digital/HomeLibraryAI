import asyncio
from typing import Optional, Any
from rembg import remove, new_session

# Lazy initialization of session - will be created on first use
_sessionHQ = None

def get_session():
    """Get or create rembg session (lazy initialization)"""
    global _sessionHQ
    if _sessionHQ is None:
        _sessionHQ = new_session('birefnet-general')
    return _sessionHQ

# Semaphore to limit concurrent rembg operations to 1
_rembg_semaphore = asyncio.Semaphore(1)

# Counter for tracking queue position
_queue_counter = 0
_queue_lock = asyncio.Lock()

# Get current queue size
async def get_queue_size() -> int:
    async with _queue_lock:
        return _queue_counter

# Asynchronous wrapper for the remove function from rembg with queue management
# param input_data: Byte representation of the input image
# param executor: Executor for running synchronous code (default is ThreadPoolExecutor)
# param kwargs: Additional arguments for the original remove function
# return: Byte representation of the processed image
async def async_remove(
    input_data: bytes,
    executor: Optional[Any] = None,
    **kwargs
) -> bytes:

    # Increment queue counter
    async with _queue_lock:
        global _queue_counter
        _queue_counter += 1

    try:
        # Wait for semaphore (queue processing)
        async with _rembg_semaphore:
            loop = asyncio.get_running_loop()
            
            # Run the synchronous function in the executor
            result = await loop.run_in_executor(
                executor,
                lambda: remove(input_data, **kwargs)
            )
            
            return result
    finally:
        # Decrement queue counter
        async with _queue_lock:
            _queue_counter -= 1