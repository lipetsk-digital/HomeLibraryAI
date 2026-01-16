import modules.engine_max as engm # For max engine functions and definitions
import modules.engine_common as engc # For common engine functions and definitions

from maxapi import Bot, Dispatcher, F
from maxapi.types import MessageCreated

bot = Bot(engm.MAX_TOKEN)
dp = Dispatcher()

@dp.message_created(F.message.body.text)
async def echo(event: MessageCreated):
    await event.message.answer(f"Повторяю за вами: {event.message.body.text}")


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())