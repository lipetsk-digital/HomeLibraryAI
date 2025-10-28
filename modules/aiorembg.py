import asyncio
from typing import Optional, Any
from rembg import remove, new_session

sessionHQ = new_session('birefnet-general')

# Asynchronous wrapper for the remove function from rembg
# param input_data: Byte representation of the input image
# param executor: Executor for running synchronous code (default is ThreadPoolExecutor)
# param kwargs: Additional arguments for the original remove function
# return: Byte representation of the processed image
async def async_remove(
    input_data: bytes,
    executor: Optional[Any] = None,
    **kwargs
) -> bytes:

    loop = asyncio.get_running_loop()
    
    # Run the synchronous function in the executor
    result = await loop.run_in_executor(
        executor,
        lambda: remove(input_data, **kwargs)
    )
    
    return result