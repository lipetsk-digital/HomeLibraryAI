# PostgreSQL Storage для maxapi

Модуль расширения библиотеки maxapi, который обеспечивает персистентное хранение состояний и данных FSM-бота в PostgreSQL.

## Проблема

Стандартный `MemoryContext` из maxapi хранит данные в оперативной памяти, что приводит к их потере при перезагрузке бота.

## Решение

Модуль `maxstorage.py` предоставляет три класса:

- **PostgresStorage** - глобальный менеджер подключений к базе данных
- **PostgresContext** - наследник `MemoryContext`, который сохраняет данные в PostgreSQL
- **PostgresDispatcher** - наследник `Dispatcher`, который использует `PostgresContext`

## Архитектура

```
PostgresStorage (singleton)
    │
    ├── Управляет connection pool
    ├── Создаёт таблицы при инициализации
    └── Используется PostgresDispatcher
         │
         └── PostgresDispatcher (extends Dispatcher)
              ├── Переопределяет __get_memory_context()
              └── Создаёт PostgresContext для каждого пользователя
                   │
                   └── PostgresContext (для каждого пользователя)
                        ├── Наследует MemoryContext
                        ├── Переопределяет методы для работы с PostgreSQL
                        └── Безопасен для параллельной работы (использует asyncio.Lock)
```

## Использование

### 1. Инициализация

```python
from modules.maxstorage import PostgresStorage, PostgresDispatcher
from maxapi import Bot

# Создаём storage
storage = PostgresStorage(
    host='localhost',
    port=5432,
    database='maxapi_fsm',
    user='bot',
    password='password'
)

# Инициализируем (создаём таблицы)
await storage.init()

# Создаём диспетчер с PostgreSQL storage
bot = Bot(token="YOUR_TOKEN")
dp = PostgresDispatcher(storage=storage)
```

### 2. Использование в обработчиках

```python
from maxapi import F
from maxapi.types import MessageCreated

@dp.message_created(F.message.body.text)
async def handler(event: MessageCreated, context):
    # Работаем с context как обычно
    data = await context.get_data()
    await context.update_data(name="John")
    await context.set_state(SomeState.waiting)
    
    # Данные автоматически сохраняются в PostgreSQL!
```

### 3. Закрытие соединения

```python
# При остановке бота
await storage.close()
```

## API PostgresContext

Все методы аналогичны `MemoryContext`:

- `async get_data() -> dict` - получить данные контекста
- `async set_data(data: dict)` - установить данные контекста
- `async update_data(**kwargs)` - обновить данные (merge)
- `async get_state() -> Optional[State|str]` - получить текущее состояние
- `async set_state(state)` - установить состояние
- `async clear()` - очистить всё (состояние + данные)

## Таблицы в базе данных

Модуль автоматически создаёт две таблицы:

### maxapi_states
```sql
CREATE TABLE "maxapi_states" (
    "chat_id" BIGINT NOT NULL,
    "user_id" BIGINT NOT NULL,
    "state" TEXT,
    PRIMARY KEY ("chat_id", "user_id")
)
```

### maxapi_data
```sql
CREATE TABLE "maxapi_data" (
    "chat_id" BIGINT NOT NULL,
    "user_id" BIGINT NOT NULL,
    "data" JSON,
    PRIMARY KEY ("chat_id", "user_id")
)
```

## Преимущества

✅ **Персистентность** - данные не теряются при перезагрузке  
✅ **Потокобезопасность** - корректно работает с множеством пользователей  
✅ **Совместимость** - полностью совместим с API MemoryContext  
✅ **Масштабируемость** - использует connection pool  
✅ **Изоляция** - каждый пользователь имеет свой изолированный контекст  

## Миграция с MemoryContext

Просто замените:

```python
# Было
from maxapi import Dispatcher
dp = Dispatcher()  # использует MemoryContext по умолчанию

# Стало
from modules.maxstorage import PostgresStorage, PostgresDispatcher

storage = PostgresStorage(host='localhost', port=5432, database='maxapi_fsm', user='bot', password='password')
await storage.init()
dp = PostgresDispatcher(storage=storage)
```

Код обработчиков остаётся без изменений!

## Как это работает

`PostgresDispatcher` использует приём **name mangling** в Python для переопределения приватного метода `__get_memory_context()` из родительского класса `Dispatcher`. 

Когда диспетчер обрабатывает событие, он вызывает этот метод для получения контекста пользователя. Наша переопределённая версия создаёт `PostgresContext` вместо `MemoryContext`, что обеспечивает сохранение данных в PostgreSQL.

## Пример

См. полный пример в [examples/maxapi_postgres_example.py](../examples/maxapi_postgres_example.py)
