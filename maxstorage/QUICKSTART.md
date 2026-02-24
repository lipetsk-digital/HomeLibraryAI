# Быстрый старт PostgreSQL Storage для maxapi

## Установка зависимостей

```bash
pip install maxapi asyncpg
```

## Минимальный пример

```python
import asyncio
from maxapi import Bot, Dispatcher, F
from maxapi.types import MessageCreated
from modules.maxstorage import PostgresStorage, PostgresContext

# Storage и dispatcher
storage = PostgresStorage(
    host='localhost',
    port=5432,
    database='maxapi_fsm',
    user='bot',
    password='password'
)

bot = Bot(token="YOUR_TOKEN")
dp = Dispatcher(storage=PostgresContext, postgres_storage=storage)

# Обработчик
@dp.message_created(F.message.body.text)
async def echo(event: MessageCreated, context):
    await context.update_data(last_message=event.message.body.text)
    data = await context.get_data()
    await event.message.answer(f"Сохранено: {data}")

# Запуск
async def main():
    await storage.init()
    try:
        await dp.start_polling(bot)
    finally:
        await storage.close()

asyncio.run(main())
```

## Настройка PostgreSQL

```sql
-- Создайте базу данных
CREATE DATABASE maxapi_fsm;

-- Создайте пользователя
CREATE USER bot WITH PASSWORD 'password';

-- Дайте права
GRANT ALL PRIVILEGES ON DATABASE maxapi_fsm TO bot;
```

Таблицы создаются автоматически при вызове `await storage.init()`

## API Context

```python
# Получить данные
data = await context.get_data()  # dict

# Установить данные
await context.set_data({"key": "value"})

# Обновить данные (merge)
await context.update_data(name="John", age=30)

# Состояние
await context.set_state(MyState.waiting)
state = await context.get_state()

# Очистить всё
await context.clear()
```

## Интеграция в существующий проект

Измените только инициализацию диспетчера:

```python
# Было:
from maxapi import Dispatcher
dp = Dispatcher()

# Стало:
from maxapi import Dispatcher
from modules.maxstorage import PostgresStorage, PostgresContext

storage = PostgresStorage(host='localhost', port=5432, database='maxapi_fsm', user='bot', password='password')
await storage.init()
dp = Dispatcher(storage=PostgresContext, postgres_storage=storage)
```

Всё остальное работает без изменений!
