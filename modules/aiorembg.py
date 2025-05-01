import asyncio
from typing import Optional, Any
from rembg import remove

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
    
    # Запуск синхронной функции в executor'е
    result = await loop.run_in_executor(
        executor,
        lambda: remove(input_data, **kwargs)
    )
    
    return result